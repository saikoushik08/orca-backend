import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # 1. ADD THIS IMPORT
from app.api.routes import health, upload, jobs  

# Ensure the outputs directory exists so FastAPI doesn't crash on startup
os.makedirs("outputs", exist_ok=True)

app = FastAPI(
    title="ORCA Backend",
    description="Object Reconstruction via Computational AI",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. ADD THIS MOUNT COMMAND
# This makes the local "outputs" folder available at the "/outputs" URL
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

@app.get("/")
def root():
    return {"status": "ORCA backend running"}

# Routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(jobs.router)