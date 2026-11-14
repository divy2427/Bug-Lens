from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from app.scanner import scan_website

app = FastAPI(title="BugLens", description="A focused website health scanner")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class ScanRequest(BaseModel):
    url: str
    max_pages: int = 10

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "BugLens"}

@app.post("/api/scan")
def scan(request: ScanRequest):
    if not 1 <= request.max_pages <= 20:
        raise HTTPException(status_code=400, detail="max_pages must be between 1 and 20")
    try:
        return scan_website(request.url, request.max_pages)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Scan failed unexpectedly. Please try another public website.")

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def home():
    return FileResponse("frontend/index.html")
