import time
import sys

def time_import(module_name):
    start = time.time()
    print(f"Importing {module_name}...", end="", flush=True)
    __import__(module_name)
    print(f" done in {time.time() - start:.2f}s")

print("Detailed Import Timing:")
time_import("logging")
time_import("fastapi")
time_import("routes.audio")
time_import("routes.text")
time_import("main")

print("All imports complete.")
