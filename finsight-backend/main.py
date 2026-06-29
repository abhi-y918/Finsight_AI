# main.py
# ─────────────────────────────────────────────────────────────────
# FASTAPI APPLICATION ENTRY POINT
#
# This is the file you run to start the server:
#   uvicorn main:app --reload --port 8000
#
# WHAT HAPPENS AT STARTUP:
#   1. FastAPI app is created
#   2. CORS is configured (so React frontend can call us)
#   3. Routes are registered
#   4. Server starts listening on port 8000
#
# WHAT IS CORS?
#   Browser security blocks requests from one origin to another.
#   e.g. http://localhost:5173 (React) → http://localhost:8000 (FastAPI)
#   CORS middleware tells the browser: "yes, this is allowed."
#   In production you'd restrict origins to your actual domain.
# ─────────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from config import settings

# ── Create FastAPI app ────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered bank statement analyzer",
    version="1.0.0",
    # Swagger UI available at: http://localhost:8000/docs
    # ReDoc available at:      http://localhost:8000/redoc
)

# ── CORS Middleware ───────────────────────────────────────────────
# Allows the React frontend (running on port 5173) to call our API.
# In production: replace "*" with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server
        "http://localhost:3000",    # Create React App (if used)
        "https://finsight.vercel.app",  # Production (Phase 4)
    ],
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, PUT, DELETE etc.
    allow_headers=["*"],
)

# ── Register routes ───────────────────────────────────────────────
# prefix="/api/v1" means all routes become:
#   /api/v1/health
#   /api/v1/analyze
app.include_router(router, prefix="/api/v1")


# ── Root endpoint ─────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# ── Run directly (for development) ───────────────────────────────
# You can also just run: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True     # Auto-restart when you save a file
    )