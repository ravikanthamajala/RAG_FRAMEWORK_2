import importlib
import threading
import time

modules = [
    'app.routes.upload',
    'app.routes.query',
    'app.routes.analysis',
    'app.routes.advanced',
    'app.routes.forecast',
    'app.routes.smart_upload',
    'app.routes.test_charts',
    'app.routes.forecast_insights',
    'app.routes.policy_simulation',
    'app.routes.explanation_evaluation',
]

for name in modules:
    result = {'done': False, 'error': None}
    def target():
        try:
            importlib.import_module(name)
        except Exception as exc:
            result['error'] = repr(exc)
        finally:
            result['done'] = True
    thread = threading.Thread(target=target, daemon=True)
    start = time.time()
    thread.start()
    thread.join(10)
    elapsed = time.time() - start
    if not result['done']:
        print(f'{name}: HANG after {elapsed:.1f}s')
        break
    if result['error']:
        print(f'{name}: ERROR {result["error"]}')
    else:
        print(f'{name}: OK {elapsed:.2f}s')
