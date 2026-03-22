"""
Intelligent Document Upload & Forecasting Route

Integrates document processing with automatic ML forecasting.
- Uploads Excel/PDF files
- Extracts numerical data
- Trains forecasting models (Prophet, ARIMA, XGBoost)
- Returns predictions with accuracy metrics
- Provides policy analysis and strategic insights
"""

from flask import Blueprint, request, jsonify, current_app
from app.utils.document_processor import process_document, allowed_file
from app.utils.data_extractor import DataExtractor
from app.services.forecasting_service import ForecastingService
from app.services.forecasting_service_v2 import AdvancedForecastingService
from app.schemas.forecast import ForecastRequest, ForecastResult, EnsembleForecastResult
from app.models.document import Document
from app.utils.embeddings import generate_embedding
from app.agents.policy_analyzer import PolicyAnalyzer
from app.utils.policy_visualizer import PolicyVisualizer
import os
import traceback
from difflib import SequenceMatcher
import json
import numpy as np
import pandas as pd
from pydantic import ValidationError

# Create smart upload blueprint
smart_upload_bp = Blueprint('smart_upload', __name__)


def clean_for_json(obj):
    """Convert NaN, Inf and other non-JSON-serializable values to JSON-safe types."""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj):
            return None
        elif np.isinf(obj):
            return str(obj)
        return obj
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if np.isnan(obj):
            return None
        elif np.isinf(obj):
            return str(obj)
        return float(obj)
    return obj


@smart_upload_bp.route('/upload-and-forecast', methods=['POST', 'OPTIONS'])
def upload_and_forecast():
    """
    Upload document and automatically forecast if numerical data found.

    Request:
        - files: Excel/PDF files to upload
        - forecast_periods (optional): Number of periods to forecast (default 36)
        - auto_select (optional): Auto-select first time series for forecasting (default true)

    Returns:
        JSON with:
        - document metadata
        - extracted numerical data
        - forecasting results with accuracy metrics
        - model comparison
    """
    
    def _select_best_candidate(candidates, target: str):
        """Pick the time series candidate that best matches the user's target."""
        best = None
        best_score = 0.0
        target_lower = target.lower()
        target_tokens = set([t for t in target_lower.split() if len(t) > 2])  # Filter short words

        for cand in candidates:
            # Use column, sheet, and any metadata as match context
            context = f"{cand.get('value_column', '')} {cand.get('sheet', '')} {cand.get('date_column', '')}".lower()
            
            # Basic string similarity
            ratio = SequenceMatcher(None, target_lower, context).ratio()
            
            # Token matching (keywords in target found in context)
            context_words = set(context.split())
            token_hits = len(target_tokens & context_words)
            
            # Weighted score: similarity + token overlap
            score = (ratio * 0.5) + (token_hits * 0.2)
            
            # Bonus if sheet name contains meaningful keywords
            sheet_name = cand.get('sheet', '').lower()
            if any(keyword in sheet_name for keyword in ['sales', 'data', 'csv', 'numbers']):
                score += 0.1
            
            if score > best_score:
                best_score = score
                best = cand

        return best, best_score

    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204

    # Validate files
    if 'files[]' not in request.files and 'files' not in request.files and 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    files = (
        request.files.getlist('files[]')
        or request.files.getlist('files')
        or request.files.getlist('file')
    )
    files = [f for f in files if f.filename != '']

    if not files:
        return jsonify({'error': 'No selected files'}), 400

    # Get optional parameters
    forecast_periods = int(request.form.get('forecast_periods', 36))
    auto_select = request.form.get('auto_select', 'true').lower() == 'true'
    forecast_target = (request.form.get('forecast_target') or '').strip()

    # Process results
    results = {
        'documents': [],
        'forecasts': [],
        'summary': {
            'files_processed': 0,
            'files_with_forecasts': 0,
            'total_models_trained': 0
        }
    }

    # Process each file
    for file in files:
        try:
            if not allowed_file(file.filename):
                results['documents'].append({
                    'filename': file.filename,
                    'status': 'failed',
                    'error': 'File type not allowed (use PDF, XLSX, XLS, CSV)'
                })
                continue

            # Step 1: Process document
            text, filename = process_document(file)
            
            # Step 2: Generate embedding for RAG
            embedding = generate_embedding(text)
            
            # Step 3: Store in MongoDB
            doc_data = {
                'filename': filename,
                'content': text,
                'embedding': embedding
            }
            Document.insert_document(doc_data)

            # Step 4: Extract numerical data
            upload_path = os.path.join('uploads', filename)
            if filename.endswith('.pdf'):
                extracted = DataExtractor.extract_from_pdf(upload_path)
            elif filename.endswith('.csv'):
                extracted = DataExtractor.extract_from_csv(upload_path)
            else:
                extracted = DataExtractor.extract_from_excel(upload_path)

            doc_result = {
                'filename': filename,
                'status': 'success' if extracted.get('success') else 'failed',
                'extraction': {
                    'success': extracted.get('success'),
                    'sheets': list(extracted.get('sheets', {}).keys()) if 'sheets' in extracted else None,
                    'numerical_summary': extracted.get('numerical_summary', {}),
                    'time_series_candidates': extracted.get('time_series_candidates', [])
                }
            }

            results['documents'].append(doc_result)
            results['summary']['files_processed'] += 1

            # Step 5: Attempt forecasting if data available
            candidates = extracted.get('time_series_candidates', []) if extracted.get('success') else []
            current_app.logger.debug("%s: Found %s time series candidates", filename, len(candidates))
            if candidates:
                current_app.logger.debug("%s: Candidates = %s", filename, candidates)
            
            if candidates:
                # If user provided a target, score; otherwise default to first candidate
                if forecast_target:
                    ts_info, match_score = _select_best_candidate(candidates, forecast_target)
                    # Lowered threshold from 0.3 to 0.15 for better matching
                    threshold_ok = match_score is None or match_score >= 0.15
                    current_app.logger.debug(
                        "%s: Match score=%s, threshold_ok=%s",
                        filename,
                        match_score,
                        threshold_ok
                    )
                else:
                    ts_info, match_score, threshold_ok = candidates[0], None, True

                if ts_info and threshold_ok:
                    current_app.logger.debug("%s: Preparing forecast for %s", filename, ts_info)
                    doc_result['selected_series'] = {
                        'sheet': ts_info['sheet'],
                        'date_column': ts_info['date_column'],
                        'value_column': ts_info['value_column'],
                        'match_score': round(match_score, 3) if match_score is not None else None,
                        'target': forecast_target or None
                    }

                    try:
                        df = DataExtractor.prepare_for_forecasting(
                            extracted,
                            sheet_name=ts_info['sheet'],
                            date_col=ts_info['date_column'],
                            value_col=ts_info['value_column']
                        )
                        current_app.logger.debug(
                            "%s: DataFrame prepared, shape=%s",
                            filename,
                            df.shape if df is not None else 'None'
                        )

                        if df is not None and len(df) > 5:
                            current_app.logger.debug(
                                "%s: Training models on %s data points...",
                                filename,
                                len(df)
                            )
                            
                            # Use advanced forecasting service
                            advanced_forecaster = AdvancedForecastingService()
                            
                            try:
                                # Assess data quality first
                                quality_metrics = advanced_forecaster.assess_data_quality(df)
                                current_app.logger.info(
                                    "%s: Data quality score=%.2f",
                                    filename,
                                    quality_metrics.quality_score
                                )
                                
                                # Forecast with validation and ensemble
                                ensemble_result = advanced_forecaster.forecast_with_validation(
                                    df,
                                    periods=forecast_periods,
                                    model_type='ensemble'
                                )
                                
                                current_app.logger.debug(
                                    "%s: Ensemble forecast complete! Best model=%s, R²=%.4f",
                                    filename,
                                    ensemble_result.best_model,
                                    ensemble_result.ensemble_metrics.r2_score
                                )
                                
                                # Convert Pydantic models to dict for JSON serialization
                                forecast_result = {
                                    'filename': filename,
                                    'data_series': f"{ts_info['value_column']} from {ts_info['sheet']}",
                                    'data_points': len(df),
                                    'date_range': ts_info['date_range'],
                                    'models_comparison': {
                                        'ensemble': {
                                            'status': 'success',
                                            'best_model': ensemble_result.best_model,
                                            'weights': ensemble_result.weights,
                                            'forecast_data': [p.dict() for p in ensemble_result.ensemble_forecast],
                                            'metrics': ensemble_result.ensemble_metrics.dict()
                                        },
                                        'comparison': {
                                            name: {
                                                'status': result.status,
                                                'forecast_data': [p.dict() for p in result.forecast_points],
                                                'metrics': result.metrics.dict(),
                                                'feature_importance': result.feature_importance
                                            }
                                            for name, result in ensemble_result.individual_models.items()
                                        }
                                    },
                                    'data_quality': quality_metrics.dict(),
                                    'best_model': ensemble_result.best_model,
                                    'best_r2_score': round(ensemble_result.ensemble_metrics.r2_score, 4),
                                    'target': forecast_target or None,
                                    'match_score': round(match_score, 3) if match_score is not None else None
                                }
                                
                                results['forecasts'].append(forecast_result)
                                results['summary']['files_with_forecasts'] += 1
                                results['summary']['total_models_trained'] += len(ensemble_result.individual_models)
                                
                            except ValueError as ve:
                                # Data quality too low
                                current_app.logger.warning(
                                    "%s: Data quality check failed: %s",
                                    filename,
                                    str(ve)
                                )
                                doc_result['selected_series']['error'] = f"Data quality issue: {str(ve)}"
                            except ValidationError as val_err:
                                # Pydantic validation failed
                                current_app.logger.error(
                                    "%s: Validation error: %s",
                                    filename,
                                    str(val_err)
                                )
                                doc_result['selected_series']['error'] = f"Validation failed: {str(val_err)}"
                        else:
                            current_app.logger.debug(
                                "%s: Insufficient data points (got %s, need >5)",
                                filename,
                                len(df) if df is not None else 0
                            )
                            doc_result['selected_series']['status'] = 'insufficient_data'
                    except Exception as forecast_error:
                        current_app.logger.error(
                            "%s: Forecasting failed - %s",
                            filename,
                            str(forecast_error)
                        )
                        current_app.logger.debug(traceback.format_exc())
                        doc_result['selected_series']['error'] = str(forecast_error)
                else:
                    doc_result['selected_series'] = {'status': 'no_match', 'target': forecast_target or None}

        except Exception as e:
            current_app.logger.error("Error processing %s: %s", file.filename, str(e))
            current_app.logger.debug(traceback.format_exc())
            results['documents'].append({
                'filename': file.filename,
                'status': 'error',
                'error': str(e)
            })

    # Always return 200 with structured status; caller can inspect summary/status instead of failing hard
    if results['summary']['files_processed'] == 0:
        results['status'] = 'no_files_processed'
        results['message'] = 'No files were processed. Check file field names and allowed types (PDF/XLSX/XLS).'
    else:
        results['status'] = 'ok'

    # Add policy insights if forecasts were generated
    if results['forecasts'] and len(results['forecasts']) > 0:
        try:
            current_app.logger.info("Generating policy insights...")
            policy_analyzer = PolicyAnalyzer()
            policy_visualizer = PolicyVisualizer()
            
            # Get document context for policy analysis
            doc_context = ""
            for doc in results['documents']:
                if doc.get('status') == 'success' and doc.get('text'):
                    doc_context += doc['text'][:5000] + "\n\n"  # Limit context size
            
            # Use first forecast for correlation
            first_forecast = results['forecasts'][0]
            
            # Get comprehensive policy analysis
            policy_insights = policy_analyzer.analyze_comprehensive_policy_impact(
                context=doc_context or "India automotive and EV market analysis with focus on policy impact and growth forecasts for 2024-2030",
                query="Analyze automotive/EV policies adopted from China, their impact on market forecast, and strategic recommendations for India",
                forecast_data=first_forecast
            )
            
            # Generate policy visualizations
            policy_charts = []
            
            # Timeline chart
            if policy_insights.get('policies_adopted_from_china'):
                timeline_chart = policy_visualizer.create_policy_adoption_timeline(
                    policy_insights['policies_adopted_from_china']
                )
                policy_charts.append({
                    'type': 'timeline',
                    'title': 'Policy Adoption Timeline: China → India',
                    'description': 'When and how India adopted key automotive policies from China',
                    'image': timeline_chart
                })
            
            # Contribution waterfall chart
            if policy_insights.get('policy_contribution_breakdown'):
                waterfall_chart = policy_visualizer.create_contribution_waterfall(
                    policy_insights['policy_contribution_breakdown']
                )
                policy_charts.append({
                    'type': 'waterfall',
                    'title': 'Policy Contribution to 2030 Forecast',
                    'description': 'Breakdown of how each policy category influences market growth',
                    'image': waterfall_chart
                })
            
            # Strategic roadmap
            if policy_insights.get('strategic_recommendations'):
                roadmap_chart = policy_visualizer.create_strategic_roadmap(
                    policy_insights['strategic_recommendations']
                )
                policy_charts.append({
                    'type': 'roadmap',
                    'title': 'Strategic Policy Implementation Roadmap',
                    'description': 'Timeline and priorities for new policy initiatives',
                    'image': roadmap_chart
                })
            
            # Gap analysis
            if policy_insights.get('policy_gaps') and policy_insights.get('policies_adopted_from_china'):
                gap_chart = policy_visualizer.create_policy_gap_analysis(
                    policy_insights['policy_gaps'],
                    policy_insights['policies_adopted_from_china']
                )
                policy_charts.append({
                    'type': 'gap_analysis',
                    'title': 'Policy Gap Analysis',
                    'description': 'Identified gaps vs successfully adopted policies',
                    'image': gap_chart
                })
            
            # Add to results
            results['policy_insights'] = policy_insights
            results['policy_charts'] = policy_charts
            
            current_app.logger.info("Policy insights generated successfully with %d charts", len(policy_charts))
            
        except Exception as e:
            current_app.logger.error("Failed to generate policy insights: %s", str(e))
            current_app.logger.debug(traceback.format_exc())
            # Don't fail the entire request if policy analysis fails
            results['policy_insights'] = {'error': str(e)}

    # Clean results of any NaN/Inf values before returning
    results = clean_for_json(results)
    return jsonify(results), 200


@smart_upload_bp.route('/forecast-from-document/<doc_id>', methods=['POST', 'OPTIONS'])
def forecast_from_document(doc_id):
    """
    Generate forecast from an already uploaded document.

    Args:
        doc_id: MongoDB document ID
        sheet_name (query): Excel sheet name (for multi-sheet files)
        date_column (query): Date column name
        value_column (query): Value column name
        periods (query): Number of periods to forecast

    Returns:
        JSON with forecast results and accuracy metrics
    """
    
    if request.method == 'OPTIONS':
        return '', 204

    try:
        # Get parameters
        sheet_name = request.args.get('sheet_name')
        date_column = request.args.get('date_column')
        value_column = request.args.get('value_column')
        periods = int(request.args.get('periods', 36))

        # Retrieve document
        doc = Document.find_by_id(doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404

        # Extract and prepare data
        filename = doc.get('filename', '')
        uploads_path = os.path.join('uploads', filename)

        if filename.endswith('.pdf'):
            extracted = DataExtractor.extract_from_pdf(uploads_path)
        else:
            extracted = DataExtractor.extract_from_excel(uploads_path)

        if not extracted.get('success'):
            return jsonify({'error': 'Failed to extract data from document'}), 400

        # Prepare for forecasting
        df = DataExtractor.prepare_for_forecasting(
            extracted,
            sheet_name=sheet_name,
            date_col=date_column,
            value_col=value_column
        )

        if df is None:
            return jsonify({'error': 'Could not prepare data for forecasting'}), 400

        # Use advanced forecasting service
        advanced_forecaster = AdvancedForecastingService()
        
        # Assess quality and forecast
        quality_metrics = advanced_forecaster.assess_data_quality(df)
        ensemble_result = advanced_forecaster.forecast_with_validation(
            df,
            periods=periods,
            model_type='ensemble'
        )

        return jsonify({
            'document': filename,
            'status': 'success',
            'forecast_results': {
                'ensemble': {
                    'best_model': ensemble_result.best_model,
                    'weights': ensemble_result.weights,
                    'forecast_data': [p.dict() for p in ensemble_result.ensemble_forecast],
                    'metrics': ensemble_result.ensemble_metrics.dict()
                },
                'comparison': {
                    name: {
                        'status': result.status,
                        'forecast_data': [p.dict() for p in result.forecast_points],
                        'metrics': result.metrics.dict(),
                        'feature_importance': result.feature_importance,
                        'shap_values': result.shap_values
                    }
                    for name, result in ensemble_result.individual_models.items()
                }
            },
            'data_summary': {
                'historical_points': len(df),
                'forecast_periods': periods,
                'best_model': ensemble_result.best_model,
                'best_r2_score': round(ensemble_result.ensemble_metrics.r2_score, 4),
                'data_quality': quality_metrics.dict()
            }
        }), 200

    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@smart_upload_bp.route('/extraction-summary', methods=['POST', 'OPTIONS'])
def extraction_summary():
    """
    Quick summary of numerical data extraction without forecasting.
    """
    
    if request.method == 'OPTIONS':
        return '', 204

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Process and extract
        text, filename = process_document(file)
        
        if filename.endswith('.pdf'):
            extracted = DataExtractor.extract_from_pdf(os.path.join('uploads', filename))
        else:
            extracted = DataExtractor.extract_from_excel(os.path.join('uploads', filename))

        return jsonify({
            'filename': filename,
            'extraction_success': extracted.get('success'),
            'summary': {
                'sheets': list(extracted.get('sheets', {}).keys()),
                'numerical_columns': extracted.get('numerical_summary', {}),
                'time_series_candidates': extracted.get('time_series_candidates', []),
                'total_numerical_values': len(extracted.get('numerical_values', []))
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
