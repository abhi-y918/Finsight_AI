# api/routes.py
# ─────────────────────────────────────────────────────────────────
# FASTAPI ROUTES — The HTTP endpoints the frontend talks to
#
# PHASE 1 ENDPOINTS:
#   POST /analyze   ← Upload PDF, run pipeline, return result
#   GET  /health    ← Check if server is running
#
# PHASE 2 will add:
#   GET  /status/{job_id}   ← Poll pipeline progress
#   GET  /result/{job_id}   ← Get completed analysis
#
# HOW FASTAPI ROUTING WORKS:
#   @router.post("/analyze")  ← decorator registers the route
#   async def analyze(...)    ← the function handles the request
#   FastAPI automatically:
#     - Parses the request
#     - Validates types
#     - Returns JSON
#     - Generates docs at /docs
# ─────────────────────────────────────────────────────────────────

import uuid
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from agents.pipeline import run_pipeline
from api.schemas import AnalyzeResponse, StatusResponse, ErrorResponse
from config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    Frontend or monitoring can ping this to verify the server is up.
    Returns: { "status": "ok", "service": "FinSight AI" }
    """
    return {"status": "ok", "service": settings.APP_NAME}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_statement(file: UploadFile = File(...)):
    """
    Main endpoint: accept a bank statement PDF, run the agent pipeline,
    return structured financial analysis.

    FLOW:
    1. Validate the uploaded file (type, size)
    2. Save to a temp file on disk (pdfplumber needs a file path)
    3. Run the LangGraph pipeline
    4. Return the result

    WHY TEMP FILE?
        pdfplumber.open() needs a file path, not bytes in memory.
        tempfile.NamedTemporaryFile creates a file that auto-deletes
        when we're done — no disk space leak.

    Args:
        file: The uploaded PDF/CSV file from the frontend

    Returns:
        AnalyzeResponse with job_id, status, and full result
    """
    # ── Step 1: Validate file type ────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not supported. Use PDF or CSV."
        )

    # ── Step 2: Validate file size ────────────────────────────────
    contents = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB allowed."
        )

    # ── Step 3: Generate unique job ID ────────────────────────────
    # job_id links this upload to its results.
    # In Phase 2 this is stored in Redis/DB for async polling.
    job_id = str(uuid.uuid4())
    print(f"\n[API] New job: {job_id} | File: {file.filename} | Size: {len(contents)/1024:.1f}KB")

    # ── Step 4: Save to temp file ─────────────────────────────────
    # suffix=".pdf" ensures pdfplumber knows the file type
    # delete=False so we can pass the path to the pipeline
    # We manually delete it in the finally block
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=file_ext,
            delete=False,
            dir="/tmp"
        ) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        print(f"[API] Saved to temp: {tmp_path}")

        # ── Step 5: Run the pipeline ──────────────────────────────
        result = run_pipeline(file_path=tmp_path, job_id=job_id)

        # ── Step 6: Return response ───────────────────────────────
        return AnalyzeResponse(
            job_id=job_id,
            status="complete",
            result=result
        )

    except Exception as e:
        print(f"[API] ❌ Pipeline failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

    finally:
        # Always clean up temp file — even if an error occurred
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            print(f"[API] Cleaned up temp file: {tmp_path}")


# ── Phase 2: Uncomment these when you add async pipeline ─────────

# @router.get("/status/{job_id}", response_model=StatusResponse)
# async def get_status(job_id: str):
#     """Poll the pipeline progress for a given job."""
#     # Will read from Redis: redis_client.get(f"status:{job_id}")
#     pass

# @router.get("/result/{job_id}")
# async def get_result(job_id: str):
#     """Get the completed analysis for a given job."""
#     # Will read from PostgreSQL: db.query(Result).filter_by(job_id=job_id).first()
#     pass