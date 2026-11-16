import uvicorn
import os
import sys

workspace = os.path.dirname(os.path.abspath(__file__))
os.chdir(workspace)
if workspace not in sys.path:
    sys.path.insert(0, workspace)

if __name__ == "__main__":
    print("[NEXUS Workcell] Starting Uvicorn API server...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
