import importlib
import time
start = time.time()
importlib.import_module("app.routes.upload")
print(f"upload import OK in {time.time() - start:.2f}s")
