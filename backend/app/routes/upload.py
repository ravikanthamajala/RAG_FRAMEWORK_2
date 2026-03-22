"""
Document Upload Route for Automotive Market Research

Handles uploads of market research documents:
- PDFs: Policy documents, research papers, regulatory frameworks
- Excel files: Market data, OEM performance metrics, sales figures, EV adoption trends

Processes documents, generates embeddings, and stores in MongoDB for analysis.
"""

from flask import Blueprint, request, jsonify
from app.utils.document_processor import process_document, allowed_file, DocumentProcessingError
from app.utils.embeddings import generate_embedding, chunk_text
from app.models.document import Document
import gc
import os
import logging
import traceback

# Create upload blueprint
upload_bp = Blueprint('upload', __name__)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = int(os.getenv('MAX_SINGLE_FILE_SIZE', str(50 * 1024 * 1024)))
PROCESS_BATCH_SIZE = int(os.getenv('UPLOAD_BATCH_SIZE', '5'))
MAX_RETRY = 1
MAX_CHUNKS_PER_DOCUMENT = int(os.getenv('MAX_CHUNKS_PER_DOCUMENT', '12'))
EMBED_GC_INTERVAL = int(os.getenv('EMBED_GC_INTERVAL', '3'))


def _select_chunks_for_embedding(chunks):
    """Select a bounded set of chunks to avoid exhausting memory on large documents."""
    if len(chunks) <= MAX_CHUNKS_PER_DOCUMENT:
        return list(enumerate(chunks)), False

    if MAX_CHUNKS_PER_DOCUMENT <= 1:
        return [(0, chunks[0])], True

    selected_indexes = sorted({
        round(i * (len(chunks) - 1) / (MAX_CHUNKS_PER_DOCUMENT - 1))
        for i in range(MAX_CHUNKS_PER_DOCUMENT)
    })
    return [(index, chunks[index]) for index in selected_indexes], True


def _embed_and_store(filename: str, text: str):
    """
    Split *text* into chunks, embed each chunk, and store them individually.
    Returns (stored_chunks, was_truncated, source_chunk_count).
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty extracted text")

    chunks = chunk_text(text, chunk_size=3000, overlap=200)
    selected_chunks, truncated = _select_chunks_for_embedding(chunks)
    stored = 0
    for selected_index, (source_index, chunk) in enumerate(selected_chunks):
        try:
            if not chunk or not chunk.strip():
                logger.warning("[upload] skipping empty chunk %s for %s", source_index, filename)
                continue

            embedding = generate_embedding(chunk)
            Document.insert_document({
                'filename': filename,
                'content': chunk,
                'embedding': embedding,
                'chunk_index': selected_index,
                'total_chunks': len(selected_chunks),
                'source_chunk_index': source_index,
                'source_total_chunks': len(chunks),
                'truncated_for_upload': truncated,
            })
            stored += 1
            del embedding
            if (selected_index + 1) % EMBED_GC_INTERVAL == 0:
                gc.collect()
        except MemoryError:
            logger.exception(
                "[upload] MemoryError while embedding file=%s chunk=%s/%s",
                filename,
                selected_index + 1,
                len(selected_chunks),
            )
            if stored > 0:
                break
            raise
        except Exception as chunk_err:
            logger.exception(
                "[upload] chunk embedding/storage error file=%s chunk=%s/%s error=%s",
                filename,
                source_index,
                len(chunks),
                chunk_err,
            )
    return stored, truncated, len(chunks)


def _file_size_bytes(file_storage) -> int:
    """Safely compute uploaded file size without consuming file content."""
    try:
        pos = file_storage.stream.tell()
        file_storage.stream.seek(0, os.SEEK_END)
        size = file_storage.stream.tell()
        file_storage.stream.seek(pos, os.SEEK_SET)
        return int(size)
    except Exception:
        return int(getattr(file_storage, 'content_length', 0) or 0)


def _validate_file(file_storage):
    """Return (is_valid, message, size_bytes)."""
    if not file_storage or not file_storage.filename:
        return False, "Empty filename", 0

    if not allowed_file(file_storage.filename):
        return False, "Unsupported file type. Allowed: pdf, xlsx, xls, csv", 0

    size = _file_size_bytes(file_storage)
    if size <= 0:
        return False, "File is empty", size
    if size > MAX_FILE_SIZE_BYTES:
        return False, (
            f"File exceeds max size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB"
        ), size
    return True, "ok", size


def _process_single_file(file_storage):
    """Process + embed a single file with one retry. Returns structured dict."""
    valid, validation_msg, size = _validate_file(file_storage)
    if not valid:
        return {
            'file': file_storage.filename,
            'status': 'error',
            'message': validation_msg,
            'size_bytes': size,
        }

    last_error = "Unknown error"
    for attempt in range(MAX_RETRY + 1):
        try:
            if hasattr(file_storage, 'stream') and hasattr(file_storage.stream, 'seek'):
                file_storage.stream.seek(0)

            logger.info(
                "[upload] start file=%s size=%s attempt=%s",
                file_storage.filename,
                size,
                attempt + 1,
            )

            text, stored_filename = process_document(file_storage)
            chunk_count, was_truncated, source_chunk_count = _embed_and_store(stored_filename, text)
            if chunk_count == 0:
                raise RuntimeError("No chunks were embedded/stored")

            logger.info(
                "[upload] success file=%s stored=%s chunks=%s source_chunks=%s truncated=%s",
                file_storage.filename,
                stored_filename,
                chunk_count,
                source_chunk_count,
                was_truncated,
            )
            return {
                'file': file_storage.filename,
                'stored_filename': stored_filename,
                'status': 'success',
                'message': (
                    f'Processed successfully ({chunk_count}/{source_chunk_count} chunks stored)'
                    if was_truncated else 'Processed successfully'
                ),
                'size_bytes': size,
                'chunks': chunk_count,
                'source_chunks': source_chunk_count,
                'truncated': was_truncated,
            }
        except DocumentProcessingError as exc:
            last_error = str(exc)
            logger.error(
                "[upload] parse error file=%s attempt=%s error=%s",
                file_storage.filename,
                attempt + 1,
                last_error,
            )
        except MemoryError as exc:
            last_error = f"MemoryError: Not enough RAM to process this file. Try uploading fewer files at once or smaller files."
            logger.error(
                "[upload] MemoryError file=%s attempt=%s",
                file_storage.filename,
                attempt + 1,
            )
            gc.collect()
            break  # No point retrying a memory error
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            logger.error(
                "[upload] processing error file=%s attempt=%s error=%s",
                file_storage.filename,
                attempt + 1,
                last_error,
            )
            logger.debug(traceback.format_exc())

    return {
        'file': file_storage.filename,
        'status': 'error',
        'message': last_error,
        'size_bytes': size,
    }

@upload_bp.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    """
    Handle file upload requests.

    Processes multiple uploaded files, extracts text, generates embeddings, and stores in DB.

    Returns:
        JSON response with success/failure counts and details.
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204

    # Check if files are in request
    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    # Get files from request (support both 'files' and 'file' keys)
    files = request.files.getlist('files') or request.files.getlist('file')
    
    # Filter out empty files
    files = [f for f in files if f.filename != '']
    
    if not files:
        return jsonify({'error': 'No selected files'}), 400

    # Track results
    successful = []
    failed = []
    uploaded_files = []
    file_results = []

    # Process in batches to keep memory stable for large upload sets
    for start in range(0, len(files), PROCESS_BATCH_SIZE):
        batch = files[start:start + PROCESS_BATCH_SIZE]
        logger.info(
            "[upload] processing batch %s-%s of %s files",
            start + 1,
            start + len(batch),
            len(files),
        )

        for file in batch:
            result = _process_single_file(file)
            file_results.append(result)
            gc.collect()  # Free memory between files to prevent MemoryError buildup

            if result['status'] == 'success':
                successful.append(result['stored_filename'])
                uploaded_files.append({
                    'original_filename': result['file'],
                    'stored_filename': result['stored_filename'],
                    'chunks': result.get('chunks', 0),
                })
            else:
                failed.append({
                    'filename': result['file'],
                    'error': result['message'],
                })

    # Return results
    status_code = 200 if successful else 400
    has_errors = len(failed) > 0
    summary = (
        f"Processed {len(files)} file(s): {len(successful)} succeeded, {len(failed)} failed"
    )

    return jsonify({
        'successful': successful,
        'uploaded_files': uploaded_files,
        'failed': failed,
        'results': file_results,
        'success_count': len(successful),
        'failure_count': len(failed),
        'has_errors': has_errors,
        'message': summary,
    }), status_code


@upload_bp.errorhandler(Exception)
def handle_upload_error(exc):
    """Ensure any uncaught exception in upload routes returns JSON, not a dropped connection."""
    logger.error("[upload] unhandled error: %s", exc, exc_info=True)
    gc.collect()
    return jsonify({'error': f'Server error: {type(exc).__name__}: {exc}'}), 500