"""
Advanced Data Extraction Utilities for Numerical Analysis

Extracts structured numerical data from PDFs and Excel files
for machine learning forecasting pipelines.
"""

import pandas as pd
import numpy as np
import openpyxl
import PyPDF2
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class DataExtractor:
    """Extracts numerical data from documents for ML forecasting."""

    @staticmethod
    def extract_from_excel(file_path: str) -> Dict:
        """
        Extract structured numerical data from Excel files.

        Args:
            file_path (str): Path to Excel file

        Returns:
            dict: {
                'success': bool,
                'data': list of DataFrames,
                'sheet_names': list,
                'numerical_summary': dict
            }
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            extracted_data = {
                'success': True,
                'sheets': {},
                'numerical_summary': {},
                'time_series_candidates': []
            }

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Store original data
                extracted_data['sheets'][sheet_name] = {
                    'data': df.to_dict('records'),
                    'shape': df.shape,
                    'columns': list(df.columns)
                }

                # Extract numerical summary
                numerical_cols = df.select_dtypes(include=[np.number]).columns
                if len(numerical_cols) > 0:
                    extracted_data['numerical_summary'][sheet_name] = {
                        'columns': list(numerical_cols),
                        'statistics': df[numerical_cols].describe().to_dict()
                    }

                # Identify time series candidates (date + numeric column)
                date_cols = df.select_dtypes(include=['datetime64']).columns
                if len(date_cols) > 0 and len(numerical_cols) > 0:
                    for date_col in date_cols:
                        for num_col in numerical_cols:
                            ts_df = df[[date_col, num_col]].dropna()
                            if len(ts_df) > 3:  # Minimum data points for forecasting
                                extracted_data['time_series_candidates'].append({
                                    'sheet': sheet_name,
                                    'date_column': str(date_col),
                                    'value_column': str(num_col),
                                    'data_points': len(ts_df),
                                    'date_range': f"{ts_df[date_col].min()} to {ts_df[date_col].max()}"
                                })

            return extracted_data

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sheets': {},
                'numerical_summary': {}
            }

    @staticmethod
    def _read_csv_robust(file_path: str):
        """Read a CSV with encoding fallbacks and delimiter sniffing."""
        import csv as _csv
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'utf-16']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc, errors='replace') as fh:
                    sample = fh.read(4096)
                try:
                    dialect = _csv.Sniffer().sniff(sample, delimiters=',;\t|')
                    sep = dialect.delimiter
                except _csv.Error:
                    sep = ','
                df = pd.read_csv(file_path, sep=sep, encoding=enc, on_bad_lines='skip')
                if not df.empty and df.shape[1] > 0:
                    return df
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception:
                continue
        return pd.read_csv(file_path, sep=',', encoding='latin-1', on_bad_lines='skip')

    @staticmethod
    def extract_from_csv(file_path: str) -> Dict:
        """
        Extract structured numerical data from CSV files.

        Args:
            file_path (str): Path to CSV file

        Returns:
            dict: Extracted data with time series candidates
        """
        try:
            df = DataExtractor._read_csv_robust(file_path)
            extracted_data = {
                'success': True,
                'sheets': {},
                'numerical_summary': {},
                'time_series_candidates': []
            }

            # Store as single sheet named after the file
            sheet_name = 'CSV_Data'
            extracted_data['sheets'][sheet_name] = {
                'data': df.to_dict('records'),
                'shape': df.shape,
                'columns': list(df.columns)
            }

            # Extract numerical summary
            numerical_cols = df.select_dtypes(include=[np.number]).columns
            if len(numerical_cols) > 0:
                extracted_data['numerical_summary'][sheet_name] = {
                    'columns': list(numerical_cols),
                    'statistics': df[numerical_cols].describe().to_dict()
                }

            # Identify time series candidates (date + numeric column or index + numeric)
            date_cols = df.select_dtypes(include=['datetime64']).columns
            
            # Try to match date columns with numeric columns
            if len(date_cols) > 0 and len(numerical_cols) > 0:
                for date_col in date_cols:
                    for num_col in numerical_cols:
                        ts_df = df[[date_col, num_col]].dropna()
                        if len(ts_df) > 3:
                            extracted_data['time_series_candidates'].append({
                                'sheet': sheet_name,
                                'date_column': str(date_col),
                                'value_column': str(num_col),
                                'data_points': len(ts_df),
                                'date_range': f"{ts_df[date_col].min()} to {ts_df[date_col].max()}"
                            })
            
            # If no date columns, use first numeric + any other numeric
            elif len(numerical_cols) >= 2:
                first_num = numerical_cols[0]
                for num_col in numerical_cols[1:]:
                    ts_df = df[[first_num, num_col]].dropna()
                    if len(ts_df) > 3:
                        extracted_data['time_series_candidates'].append({
                            'sheet': sheet_name,
                            'date_column': str(first_num),
                            'value_column': str(num_col),
                            'data_points': len(ts_df),
                            'date_range': f"Index 0-{len(ts_df)-1}"
                        })
            
            # Single numeric column as time series with row index
            elif len(numerical_cols) == 1:
                num_col = numerical_cols[0]
                ts_df = df[[num_col]].dropna()
                if len(ts_df) > 3:
                    extracted_data['time_series_candidates'].append({
                        'sheet': sheet_name,
                        'date_column': 'Index',
                        'value_column': str(num_col),
                        'data_points': len(ts_df),
                        'date_range': f"Rows 0-{len(ts_df)-1}"
                    })

            return extracted_data

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sheets': {},
                'numerical_summary': {},
                'time_series_candidates': []
            }

    @staticmethod
    def extract_from_pdf(file_path: str) -> Dict:
        """
        Extract numerical data and tables from PDF files, including time series candidates.

        Args:
            file_path (str): Path to PDF file

        Returns:
            dict: Extracted numerical values, patterns, and time series candidates
        """
        try:
            extracted_data = {
                'success': True,
                'numerical_values': [],
                'tables': [],
                'patterns': {},
                'full_text': '',
                'time_series_candidates': []
            }

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    extracted_data['full_text'] += text + '\n'
                    
                    # Extract all numbers
                    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
                    extracted_data['numerical_values'].extend(
                        [{'page': page_num + 1, 'value': float(n)} for n in numbers]
                    )

            # Extract common numerical patterns
            extracted_data['patterns'] = DataExtractor._find_patterns(
                extracted_data['full_text']
            )

            # Try to infer time series candidates from patterns (years + values)
            candidates = DataExtractor._infer_time_series_from_patterns(
                extracted_data['patterns'],
                extracted_data['full_text']
            )
            extracted_data['time_series_candidates'] = candidates

            return extracted_data

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'numerical_values': [],
                'patterns': {},
                'time_series_candidates': []
            }

    @staticmethod
    def _find_patterns(text: str) -> Dict:
        """Find common numerical patterns in text."""
        patterns = {}

        # Year references
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        if years:
            patterns['years'] = list(set(years))

        # Percentage values
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
        if percentages:
            patterns['percentages'] = [float(p) for p in percentages]

        # Large numbers (sales, units, etc.)
        large_nums = re.findall(r'\b(\d{4,}(?:,\d{3})*(?:\.\d+)?)\b', text)
        if large_nums:
            patterns['large_numbers'] = [
                float(n.replace(',', '')) for n in large_nums
            ]

        # Growth/decline indicators
        growth_terms = re.findall(r'(growth|decline|increase|decrease|rise|fall)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*%?', text, re.IGNORECASE)
        if growth_terms:
            patterns['growth_indicators'] = growth_terms

        return patterns

    @staticmethod
    def _infer_time_series_from_patterns(patterns: Dict, full_text: str) -> List[Dict]:
        """Infer time series candidates from extracted patterns (years + numbers)."""
        candidates = []
        
        try:
            # Look for year-value patterns
            if 'years' in patterns and len(patterns['years']) > 2:
                years = sorted([int(y) for y in patterns['years']])
                
                # Find lines with years and numbers to build implicit time series
                lines = full_text.split('\n')
                year_value_pairs = []
                
                for line in lines:
                    for year in years:
                        if str(year) in line:
                            # Extract numbers near this year
                            nums = re.findall(r'(\d+(?:\.\d+)?)', line)
                            if nums:
                                # Skip if it's just the year itself
                                nums = [float(n) for n in nums if int(float(n)) != year]
                                if nums:
                                    year_value_pairs.append({'year': year, 'values': nums})
                
                # If we found year-value pairs, create a candidate
                if len(year_value_pairs) > 3:
                    # Create a synthetic sheet and column name
                    candidate = {
                        'sheet': 'PDF_TimeSeries',
                        'date_column': 'Year',
                        'value_column': 'Value',
                        'data_points': len(year_value_pairs),
                        'date_range': f"{year_value_pairs[0]['year']} to {year_value_pairs[-1]['year']}",
                        'source': 'pattern_inferred'
                    }
                    candidates.append(candidate)
            
            # Also check for large numbers that might be time series data
            if 'large_numbers' in patterns and len(patterns['large_numbers']) > 5:
                candidate = {
                    'sheet': 'PDF_LargeNumbers',
                    'date_column': 'Index',
                    'value_column': 'Quantity',
                    'data_points': len(patterns['large_numbers']),
                    'date_range': f"Points: {len(patterns['large_numbers'])}",
                    'source': 'large_numbers'
                }
                candidates.append(candidate)
        
        except Exception as e:
            pass
        
        return candidates

    @staticmethod
    def prepare_for_forecasting(extracted_data: Dict, sheet_name: str = None, 
                               date_col: str = None, value_col: str = None) -> Optional[pd.DataFrame]:
        """
        Prepare extracted data for ML forecasting. Handles both Excel sheets and PDF-inferred series.

        Args:
            extracted_data (dict): Output from extract_from_excel or extract_from_pdf
            sheet_name (str): Sheet to use
            date_col (str): Date column name
            value_col (str): Value column name

        Returns:
            pd.DataFrame: Prepared time series data
        """
        try:
            if not extracted_data.get('success'):
                return None

            # Auto-select first time series candidate if not specified
            if sheet_name is None and date_col is None:
                if extracted_data['time_series_candidates']:
                    ts_info = extracted_data['time_series_candidates'][0]
                    sheet_name = ts_info['sheet']
                    date_col = ts_info['date_column']
                    value_col = ts_info['value_column']
                else:
                    return None

            # Handle PDF-inferred time series (no sheets in extracted_data)
            if 'sheets' not in extracted_data or sheet_name not in extracted_data.get('sheets', {}):
                # Try to construct from patterns (PDF inferred)
                if 'patterns' in extracted_data:
                    patterns = extracted_data['patterns']

                    if sheet_name == 'PDF_TimeSeries' and 'years' in patterns:
                        years = sorted([int(y) for y in patterns['years']])
                        # Get large numbers or growth indicators as values
                        values = patterns.get('large_numbers', [])
                        if not values and 'growth_indicators' in patterns:
                            values = [float(v[1]) for v in patterns['growth_indicators'][:len(years)]]

                        if len(values) >= len(years):
                            values = values[:len(years)]

                        if len(values) > 3:
                            df = pd.DataFrame({
                                'ds': [pd.Timestamp(year=y, month=1, day=1) for y in years[:len(values)]],
                                'y': values
                            })
                            return df.sort_values('ds').reset_index(drop=True)

                    if sheet_name == 'PDF_LargeNumbers' and 'large_numbers' in patterns:
                        raw_values = patterns.get('large_numbers', [])
                        values = pd.to_numeric(pd.Series(raw_values), errors='coerce').dropna().tolist()
                        if len(values) > 3:
                            df = pd.DataFrame({
                                'ds': pd.date_range(start='2000-01-01', periods=len(values), freq='D'),
                                'y': values
                            })
                            return df.sort_values('ds').reset_index(drop=True)

                return None

            df = pd.DataFrame(extracted_data['sheets'][sheet_name]['data'])
            
            # Handle Index-based date column (for CSV with row indices)
            if date_col == 'Index':
                df['Index'] = range(len(df))
                df['Index'] = pd.to_datetime(df['Index'], unit='D')
            else:
                # Prepare for Prophet/ARIMA
                if pd.api.types.is_numeric_dtype(df[date_col]):
                    year_like = df[date_col].dropna().astype(int)
                    if year_like.between(1900, 2100).all():
                        df[date_col] = pd.to_datetime(year_like.astype(str) + '-01-01')
                    else:
                        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                else:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
            
            # Remove NaN values and sort
            df = df[[date_col, value_col]].dropna()
            df = df.sort_values(date_col).reset_index(drop=True)

            # Rename for standard ML pipeline
            df = df.rename(columns={date_col: 'ds', value_col: 'y'})

            return df

        except Exception as e:
            print(f"Error preparing data: {str(e)}")
            return None
