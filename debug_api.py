import sys
import traceback

print("Starting debug_api.py")
try:
    import uvicorn
    print("Uvicorn imported successfully.")
except Exception as e:
    print("Failed to import uvicorn:")
    traceback.print_exc()

try:
    import api
    print("api.py imported successfully!")
    print("Starting uvicorn programmatically...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
except Exception as e:
    print("Failed to import api or run uvicorn:")
    traceback.print_exc()
