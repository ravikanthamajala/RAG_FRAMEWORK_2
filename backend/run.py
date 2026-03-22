"""
Entry point for the Flask backend application.

Automotive Market Analysis Backend
Project: India Automotive Market Forecasting 2025-2030
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Fix for Pandas/NumPy hanging on Windows due to MKL initialization
os.environ.setdefault('NUMEXPR_MAX_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')

logging.getLogger('werkzeug').setLevel(logging.INFO)

# Configure logging for research reproducibility
BASE_DIR = Path(__file__).resolve().parent
log_dir = BASE_DIR / "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            str(log_dir / f"backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

from app import create_app
from wsgiref.simple_server import make_server

app = create_app()

if __name__ == '__main__':
    PORT = int(os.getenv("PORT", "4000"))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    try:
        logger.info("Starting server on port %s using wsgiref", PORT)
        logger.info("Environment: %s", os.getenv("ENVIRONMENT", "development"))

        # Use wsgiref which works reliably on Windows
        server = make_server(HOST, PORT, app)
        logger.info("Server is listening on http://localhost:%s", PORT)
        logger.info("Press Ctrl+C to stop")

        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Exception: %s: %s", type(e).__name__, e, exc_info=True)
        sys.exit(1)