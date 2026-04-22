from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from uuid import UUID
from pathlib import Path
import traceback
import asyncio

from app.jobs.job_repository import JobRepository
from app.jobs.job_manager import JobManager
from app.storage.supabase_client import supabase

router = APIRouter(
    prefix="/upload",
    tags=["Uploads"]
)

MAX_IMAGES_PER_JOB = 500
UPLOADS_ROOT = Path("uploads")


@router.post("/image/{job_id}")
async def upload_images(
    job_id: UUID,
    files: List[UploadFile] = File(...)
):
    # -----------------------------
    # 1️⃣ Validate job exists
    # -----------------------------
    job = JobRepository.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # -----------------------------
    # 2️⃣ Validate upload permission
    # -----------------------------
    if not JobManager.can_upload_images(job_id):
        raise HTTPException(
            status_code=400,
            detail=f"Uploads are locked. Job is '{job['status']}'."
        )

    # -----------------------------
    # 2.5️⃣ Move CREATED → UPLOADING
    # -----------------------------
    JobManager.mark_uploading(job_id)

    # -----------------------------
    # 3️⃣ Enforce max image limit
    # -----------------------------
    existing_count = JobRepository.count_images(job_id)
    incoming_count = len(files)

    if existing_count + incoming_count > MAX_IMAGES_PER_JOB:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Image limit exceeded. "
                f"Current: {existing_count}, "
                f"Trying to add: {incoming_count}, "
                f"Max allowed: {MAX_IMAGES_PER_JOB}"
            )
        )

    # -----------------------------
    # 4️⃣ Prepare local upload folder
    # -----------------------------
    local_images_dir = UPLOADS_ROOT / str(job_id) / "images"
    local_images_dir.mkdir(parents=True, exist_ok=True)

    uploaded_images = []

    # -----------------------------
    # 5️⃣ Upload images
    # -----------------------------
    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} is not a valid image"
            )

        storage_path = f"{job_id}/{file.filename}"
        local_file_path = local_images_dir / file.filename

        try:
            # Safely stream the file to local disk first
            with open(local_file_path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)

            # Upload to Cloud Storage
            try:
                with open(local_file_path, "rb") as f:
                    file_bytes = f.read()
                    supabase.storage.from_("orca-images").upload(storage_path, file_bytes)
                
                JobRepository.add_image(job_id, storage_path)
                
                # 🛑 FIX: Add a tiny 50ms delay between cloud uploads.
                # This prevents Supabase from dropping connections due to rapid connection bursting!
                await asyncio.sleep(0.05)

            except Exception as cloud_err:
                print(f"⚠️ Cloud sync skipped for {file.filename}: {cloud_err}")

            uploaded_images.append({
                "filename": file.filename,
                "storage_path": storage_path,
                "local_path": str(local_file_path)
            })

        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ CRITICAL ERROR saving {file.filename}:")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )

    # -----------------------------
    # 6️⃣ Return updated status
    # -----------------------------
    updated_job = JobRepository.get_job(job_id)

    return {
        "job_id": str(job_id),
        "uploaded_count": len(uploaded_images),
        "total_images": JobRepository.count_images(job_id),
        "status": updated_job["status"],
        "local_images_dir": str(local_images_dir),
        "uploaded_images": uploaded_images,
        "message": "Images uploaded successfully"
    }