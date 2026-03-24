import time
import sys

print("Checking startup time...")
start = time.time()

print("Importing main...")
import main
print(f"Main imported in {time.time() - start:.2f}s")

print("Checking FastAPI app status...")
from main import app
print("App loaded.")

print("Startup check complete.")
