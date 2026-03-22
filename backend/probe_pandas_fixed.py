import importlib
import threading
import time

start = time.time()
importlib.import_module("pandas")
print(f"pandas import OK in {time.time() - start:.2f}s", flush=True)
