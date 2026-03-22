"""
Minimal Backend Server - Emergency Mode
Starts a working backend on port 4000 immediately
Provides upload endpoint for frontend

Run this if dependencies are slow to install:
    python run_minimal.py

This will:
- Start backend on http://localhost:4000
- Provide /api/health and /api/upload endpoints
- Return 200 OK for all requests
- Allow CORS from localhost:3000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import sys

class CORSRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler with CORS support"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        path = self.path
        
        if path == '/api/health' or path == '/api/health/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
            self.end_headers()
            response = {
                'status': 'ok',
                'message': 'Backend server is running (MINIMAL MODE)',
                'service': 'agentic-rag-backend',
                'port': 4000,
                'mode': 'minimal-emergency',
            }
            self.wfile.write(json.dumps(response).encode())
        elif path == '/api/health/detailed':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
            self.end_headers()
            response = {
                'status': 'ok',
                'message': 'Backend operational in minimal mode',
                'service': 'agentic-rag-backend',
                'database': 'not-connected',
                'version': '1.0.0-minimal',
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
            self.end_headers()
            response = {'error': 'Endpoint not found'}
            self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Handle POST requests"""
        path = self.path
        
        if '/api/upload' in path:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read the body (files data)
            body = self.rfile.read(content_length)
            
            # Parse multipart form data to extract filenames
            filenames = []
            if b'filename=' in body:
                parts = body.split(b'filename=')
                for part in parts[1:]:
                    # Extract filename between quotes
                    start = part.find(b'"') + 1
                    end = part.find(b'"', start)
                    if start < end:
                        filenames.append(part[start:end].decode('utf-8', errors='ignore'))
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.end_headers()
            
            response = {
                'status': 'success',
                'message': 'Files received (MINIMAL MODE - no processing)',
                'success_count': len(filenames),
                'uploaded_files': [{'original_filename': f, 'stored_filename': f} for f in filenames],
                'successful': filenames,
                'failed': [],
                'failure_count': 0,
                'mode': 'minimal-emergency',
            }
            self.wfile.write(json.dumps(response).encode())
            
            print(f'✓ Upload received: {filenames}')
        
        elif '/api/run-simulation' in path:
            # Handle policy simulation requests
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                # Parse JSON payload
                payload = json.loads(body.decode('utf-8'))
            except:
                payload = {}
            
            # Send mock simulation response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.end_headers()
            
            charging_infra = max(0.0, min(100.0, float(payload.get('charging_infra', 50))))
            subsidies = max(0.0, min(100.0, float(payload.get('subsidies', 50))))
            manufacturing = max(0.0, min(100.0, float(payload.get('manufacturing', 50))))
            rnd = max(0.0, min(100.0, float(payload.get('rnd', 50))))
            mandates = max(0.0, min(100.0, float(payload.get('mandates', 50))))
            state_incentives = max(0.0, min(100.0, float(payload.get('state_incentives', 50))))
            new_ports    = bool(payload.get('new_ports', False))
            new_highways = bool(payload.get('new_highways', False))

            policy_score = (
                charging_infra * 0.30 +
                subsidies * 0.25 +
                manufacturing * 0.20 +
                rnd * 0.10 +
                mandates * 0.10 +
                state_incentives * 0.05
            )

            base_growth_rate = 0.05
            policy_growth_boost = (policy_score / 100.0) * 0.025
            port_construction_boost    = 0.03  if new_ports    else 0.0
            highway_construction_boost = 0.025 if new_highways else 0.0
            effective_growth_rate = base_growth_rate + policy_growth_boost + port_construction_boost + highway_construction_boost
            current_value = max(1.0, float(payload.get('current_value', 4_200_000)))
            years = list(range(2025, 2051))

            print(f'Base Growth: {base_growth_rate:.4f}')
            print(f'Policy Impact: {policy_growth_boost:.4f}')
            print(f'Port Construction Impact: {port_construction_boost:.4f}')
            print(f'Highway Construction Impact: {highway_construction_boost:.4f}')
            print(f'Final Growth: {effective_growth_rate:.4f}')
            print(f'New Ports: {new_ports}, New Highways: {new_highways}')

            without_policy = [
                round(current_value * ((1 + base_growth_rate) ** i))
                for i in range(len(years))
            ]
            with_policy = [
                round(current_value * ((1 + effective_growth_rate) ** i))
                for i in range(len(years))
            ]
            forecast_data = [
                {
                    'year': year,
                    'month': index * 12,
                    'base': without_policy[index],
                    'adjusted': with_policy[index],
                }
                for index, year in enumerate(years)
            ]
            delta = with_policy[-1] - without_policy[-1]
            
            response = {
                'status': 'success',
                'mode': 'minimal-emergency',
                'message': 'Policy simulation executed (MINIMAL MODE)',
                'input': payload,
                'years': years,
                'without_policy': without_policy,
                'with_policy': with_policy,
                'policy_score': round(policy_score, 1),
                'base_growth_rate': round(base_growth_rate * 100, 2),
                'policy_growth_boost': round(policy_growth_boost * 100, 2),
                'port_construction_boost': round(port_construction_boost * 100, 2),
                'highway_construction_boost': round(highway_construction_boost * 100, 2),
                'effective_growth_rate': round(effective_growth_rate * 100, 2),
                'result': {
                    'base_value': current_value,
                    'adjusted_value': with_policy[-1],
                    'change_percent': round((delta / without_policy[-1]) * 100, 2),
                    'scenario': ('with_new_ports_and_highways' if (new_ports and new_highways)
                                 else 'with_new_ports' if new_ports
                                 else 'with_new_highways' if new_highways
                                 else 'base_growth_only'),
                },
                'forecast_data': forecast_data,
                'debug': {
                    'base_growth': round(base_growth_rate, 4),
                    'policy_impact': round(policy_growth_boost, 4),
                    'port_impact': round(port_construction_boost, 4),
                    'highway_impact': round(highway_construction_boost, 4),
                    'final_growth': round(effective_growth_rate, 4),
                    'new_ports': new_ports,
                    'new_highways': new_highways,
                },
                'insights': [
                    f'Base growth starts at {base_growth_rate * 100:.1f}% per year.',
                    f'Policy mix adds {policy_growth_boost * 100:.2f}% annual uplift.',
                    *(
                        [f'New port construction adds {port_construction_boost * 100:.2f}% annual uplift.'] if new_ports else []
                    ),
                    *(
                        [f'New highway construction adds {highway_construction_boost * 100:.2f}% annual uplift.'] if new_highways else []
                    ),
                    *([
                        'No new infrastructure construction uplift applied.'
                    ] if not new_ports and not new_highways else []),
                    f'By 2050 the scenario creates {delta:,} additional EV units over baseline.',
                ]
            }
            self.wfile.write(json.dumps(response).encode())
            
            print(f'✓ Simulation request received: with_new_ports={new_ports}, with_new_highways={new_highways}')

        elif '/api/query-with-charts' in path or '/api/query' in path:
            # Handle document query requests in minimal mode
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                payload = json.loads(body.decode('utf-8')) if body else {}
            except Exception:
                payload = {}

            user_query = str(payload.get('query', '')).strip()
            if not user_query:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
                self.send_header('Access-Control-Allow-Credentials', 'true')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No query provided'}).encode())
                return

            q = user_query.lower()
            if any(word in q for word in ['compare', 'difference', 'vs', 'versus']):
                intent = 'COMPARISON'
                confidence = 'Medium'
                response_text = (
                    'Minimal mode response: comparison intent detected. '
                    'I can provide high-level directional guidance, but document-grounded analysis is disabled in minimal mode. '
                    'Please run the full backend for source-backed comparisons and chart generation.'
                )
            elif any(word in q for word in ['forecast', 'predict', 'projection']):
                intent = 'FORECAST'
                confidence = 'Medium'
                response_text = (
                    'Minimal mode response: forecast intent detected. '
                    'Detailed forecasting with retrieved document evidence is available in full backend mode.'
                )
            else:
                intent = 'GENERAL'
                confidence = 'Low'
                response_text = (
                    'Minimal mode response: query received. '
                    'Document retrieval and RAG reasoning are not active in emergency mode.'
                )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.end_headers()

            response = {
                'success': True,
                'mode': 'minimal-emergency',
                'response': response_text,
                'sources': [],
                'confidence': confidence,
                'confidence_reason': 'Running in emergency minimal backend without vector retrieval.',
                'intent': intent,
                'query_type': intent,
                'charts': [],
                'has_visualization': False,
            }
            self.wfile.write(json.dumps(response).encode())
            print(f'✓ Query request handled in minimal mode: intent={intent}')
        
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
            self.end_headers()
            response = {'error': 'Endpoint not found'}
            self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        """Suppress default logging"""
        if 'OPTIONS' not in str(args):
            print(f'[{self.client_address[0]}] {format % args}')


def start_server(host='0.0.0.0', port=4000):
    """Start the minimal HTTP server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    
    print(f'╔════════════════════════════════════════════════════════════╗')
    print(f'║  Agentic RAG Backend - MINIMAL MODE (Emergency)           ║')
    print(f'╠════════════════════════════════════════════════════════════╣')
    print(f'║  Server: http://{host}:{port}                             ║')
    print(f'║  Health: http://localhost:{port}/api/health               ║')
    print(f'║  Upload: http://localhost:{port}/api/upload               ║')
    print(f'│                                                            │')
    print(f'║  Status: RUNNING (no dependencies required)              ║')
    print(f'║  Mode: Minimal Emergency (accept uploads, no processing) ║')
    print(f'║                                                            ║')
    print(f'║  Install full backend in another terminal:               ║')
    print(f'║    cd backend                                             ║')
    print(f'║    pip install -r requirements.txt                       ║')
    print(f'║    python run.py                                          ║')
    print(f'╚════════════════════════════════════════════════════════════╝')
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f'\n\nShutdown requested by user.')
        httpd.shutdown()


if __name__ == '__main__':
    PORT = int(os.getenv('PORT', '4000'))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    try:
        start_server(HOST, PORT)
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f'✗ Error: Port {PORT} is already in use!')
            print(f'\nSolution:')
            print(f'  1. Find what\'s using port {PORT}:')
            print(f'     netstat -ano | findstr :{PORT}')
            print(f'  2. Kill the process:')
            print(f'     taskkill /PID <PID> /F')
            sys.exit(1)
        else:
            print(f'✗ Error: {e}')
            sys.exit(1)
