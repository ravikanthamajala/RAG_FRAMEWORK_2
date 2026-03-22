import importlib
import threading
import time

modules = [
    'app.utils.document_processor',
    'app.utils.embeddings',
    'app.models.document',
]

for name in modules:
    result = {'done': False, 'error': None}
    def target(module_name=name):
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            result['error'] = repr(exc)
        finally:
            result['done'] = True
    thread = threading.Thread(target=target, daemon=True)
    start = time.time()
    thread.start()
    thread.join(8)
    elapsed = time.time() - start
    if not result['done']:
        print(f'{name}: HANG after {elapsed:.1f}s', flush=True)
        break
    if result['error']:
        print(f'{name}: ERROR {result["error"]}', flush=True)
    else:
        print(f'{name}: OK {elapsed:.2f}s', flush=True)
