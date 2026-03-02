from fastapi import FastAPI
from app.api.routes import health, upload, jobs  

app = FastAPI(
    title="ORCA Backend",
    description="Object Reconstruction via Computational AI",
    version="0.1.0"
)

@app.get("/")
def root():
    return {"status": "ORCA backend running"}

# Routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(jobs.router)   # ✅ NO prefix here
