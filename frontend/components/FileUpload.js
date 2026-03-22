/*
 * FileUpload component for uploading documents.
 * Allows selecting and uploading PDF and Excel files to the backend.
 */

import { useRef, useState } from 'react'
import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:4000'
const UPLOAD_URL = `${API_BASE_URL}/api/upload`

export default function FileUpload({ onUpload }) {
  const [selectedFiles, setSelectedFiles] = useState([])
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [statusMessage, setStatusMessage] = useState(null)
  const fileInputRef = useRef(null)

  const getFileKey = (file) => file.name.trim().toLowerCase()

  const formatFileSize = (size) => `${(size / 1024).toFixed(2)} KB`

  const mapUploadedFiles = (selectedBatch, uploadDetails) => {
    if (!Array.isArray(uploadDetails) || uploadDetails.length === 0) {
      return selectedBatch
    }

    return uploadDetails.map((detail) => {
      const matchedFile = selectedBatch.find((file) => file.name === detail.original_filename)

      if (!matchedFile) {
        return {
          name: detail.stored_filename,
          size: 0,
          originalName: detail.original_filename,
        }
      }

      return {
        ...matchedFile,
        name: detail.stored_filename,
        originalName: detail.original_filename,
      }
    })
  }

  const handleFileChange = (e) => {
    const incomingFiles = Array.from(e.target.files || [])

    if (incomingFiles.length === 0) {
      return
    }

    setSelectedFiles((prevSelectedFiles) => {
      const existingKeys = new Set([
        ...prevSelectedFiles.map(getFileKey),
        ...uploadedFiles.map(getFileKey),
      ])
      const nextSelectedFiles = [...prevSelectedFiles]
      const skippedNames = []

      for (const file of incomingFiles) {
        const fileKey = getFileKey(file)

        if (existingKeys.has(fileKey)) {
          skippedNames.push(file.name)
          continue
        }

        existingKeys.add(fileKey)
        nextSelectedFiles.push(file)
      }

      if (skippedNames.length > 0) {
        setStatusMessage({
          type: 'warning',
          text: `Skipped duplicate file${skippedNames.length > 1 ? 's' : ''}: ${skippedNames.join(', ')}`,
        })
      } else {
        setStatusMessage(null)
      }

      return nextSelectedFiles
    })

    e.target.value = null
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      return
    }

    setUploading(true)
    setStatusMessage(null)

    try {
      const formData = new FormData()

      for (const file of selectedFiles) {
        formData.append('files', file)
      }

      const response = await axios.post(UPLOAD_URL, formData, {
        timeout: 180000,
      })

      const uploadDetails = response.data?.uploaded_files || []
      const successfulNames = new Set(response.data?.successful || selectedFiles.map((file) => file.name))
      const successfullyUploadedFiles = uploadDetails.length > 0
        ? mapUploadedFiles(selectedFiles, uploadDetails)
        : selectedFiles.filter((file) => successfulNames.has(file.name))
      const failedUploads = response.data?.failed || []
      const successCount = response.data?.success_count ?? successfullyUploadedFiles.length
      const failureCount = response.data?.failure_count ?? failedUploads.length

      setUploadedFiles((prevUploadedFiles) => [...prevUploadedFiles, ...successfullyUploadedFiles])
      onUpload?.(successfullyUploadedFiles)

      if (successfullyUploadedFiles.length > 0 && failedUploads.length === 0) {
        setStatusMessage({
          type: 'success',
          text: `Processed ${successCount} file${successCount !== 1 ? 's' : ''} successfully. Total uploaded: ${uploadedFiles.length + successfullyUploadedFiles.length}.`,
        })
      }

      if (failedUploads.length > 0) {
        setStatusMessage({
          type: 'warning',
          text: `Completed with errors: ${successCount} succeeded, ${failureCount} failed. Failed files: ${failedUploads.map((file) => `${file.filename} - ${file.error}`).join(', ')}`,
        })
      }

      setSelectedFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = null
      }
    } catch (error) {
      console.error('Upload failed:', error)
      
      // Detailed error analysis
      let errorMessage = 'Upload failed'
      let errorDetails = ''
      
      if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        errorMessage = `Network Error: Cannot reach ${UPLOAD_URL}`
        errorDetails = 'Backend server may be offline or unreachable'
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Upload Timeout'
        errorDetails = 'Request took too long - try uploading fewer files'
      } else if (error.response?.status === 404) {
        errorMessage = '404: Endpoint Not Found'
        errorDetails = `The API endpoint ${UPLOAD_URL} does not exist`
      } else if (error.response?.status === 403) {
        errorMessage = '403: CORS Error'
        errorDetails = 'Frontend cannot access backend due to CORS policy'
      } else if (error.response?.status === 500) {
        errorMessage = '500: Server Error'
        errorDetails = error.response?.data?.error || 'Backend server error occurred'
      } else if (error.response?.data?.error) {
        errorMessage = 'Server Error'
        errorDetails = error.response.data.error
      } else {
        errorMessage = 'Upload Error'
        errorDetails = error.message || 'Unknown error occurred'
      }
      
      setStatusMessage({
        type: 'error',
        text: `${errorMessage}: ${errorDetails}`,
      })
    } finally {
      setUploading(false)
    }
  }

  const handleRemoveSelectedFile = (fileName) => {
    setSelectedFiles((prevSelectedFiles) => prevSelectedFiles.filter((file) => file.name !== fileName))
  }

  const handleRemoveUploadedFile = (fileName) => {
    setUploadedFiles((prevUploadedFiles) => prevUploadedFiles.filter((file) => file.name !== fileName))
    setStatusMessage({
      type: 'warning',
      text: `${fileName} was removed from the uploaded list view.`,
    })
  }

  const openFilePicker = () => {
    fileInputRef.current?.click()
  }

  const statusStyles = {
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  }

  return (
    <div className="border-2 border-dashed border-gray-300 p-6 rounded-lg">
      <div className="mb-4">
        <div className="flex items-center justify-between gap-3 mb-2">
          <label className="block text-sm font-medium text-gray-700">
            Select Documents (PDF, Excel, CSV)
          </label>
          {uploadedFiles.length > 0 && (
            <button
              type="button"
              onClick={openFilePicker}
              className="text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              Add More Files
            </button>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.xlsx,.xls,.csv"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 border border-gray-300 rounded-lg p-2 cursor-pointer"
        />
      </div>

      {statusMessage && (
        <div className={`mb-4 rounded-lg border px-4 py-3 text-sm ${statusStyles[statusMessage.type]}`}>
          {statusMessage.text}
        </div>
      )}

      {selectedFiles.length > 0 && (
        <div className="mb-4 rounded-lg bg-blue-50 p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Selected for Next Upload ({selectedFiles.length})
          </p>
          <ul className="space-y-2">
            {selectedFiles.map((file) => (
              <li key={`${file.name}-${file.size}`} className="flex items-center justify-between gap-3 text-sm text-gray-700">
                <div className="flex items-center min-w-0">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                  <span className="truncate">
                    {file.name}
                    {file.originalName && file.originalName !== file.name ? ` (from ${file.originalName})` : ''}
                    {` (${formatFileSize(file.size)})`}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveSelectedFile(file.name)}
                  className="text-red-500 hover:text-red-600"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {uploadedFiles.length > 0 && (
        <div className="mb-4 rounded-lg bg-gray-50 p-4">
          <div className="flex items-center justify-between gap-3 mb-2">
            <p className="text-sm font-medium text-gray-700">All Uploaded Files</p>
            <span className="text-sm text-gray-500">
              {uploadedFiles.length} file{uploadedFiles.length !== 1 ? 's' : ''} uploaded
            </span>
          </div>
          <ul className="space-y-2 max-h-56 overflow-y-auto">
            {uploadedFiles.map((file) => (
              <li key={`uploaded-${file.name}-${file.size}`} className="flex items-center justify-between gap-3 text-sm text-gray-600">
                <div className="flex items-center min-w-0">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  <span className="truncate">{file.name} ({formatFileSize(file.size)})</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveUploadedFile(file.name)}
                  className="text-red-500 hover:text-red-600"
                >
                  Remove from List
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        type="button"
        onClick={handleUpload}
        disabled={selectedFiles.length === 0 || uploading}
        className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition"
      >
        {uploading
          ? 'Uploading...'
          : `Upload ${selectedFiles.length} File${selectedFiles.length !== 1 ? 's' : ''}`}
      </button>
    </div>
  )
}