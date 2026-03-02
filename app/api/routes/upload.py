from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from uuid import UUID

from app.jobs.job_repository import JobRepository
from app.jobs.job_manager import JobManager
from app.jobs.job_states import JobStatus
from app.storage.supabase_client import supabase

router = APIRouter(
    prefix="/upload",
    tags=["Uploads"]
)

MAX_IMAGES_PER_JOB = 100


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
    # ✅ 2.5️⃣ Move CREATED → UPLOADING (once)
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

    uploaded_images = []

    # -----------------------------
    # 4️⃣ Upload images
    # -----------------------------
    for file in files:
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} is not a valid image"
            )

        storage_path = f"{job_id}/{file.filename}"

        try:
            contents = await file.read()

            # Upload to Supabase Storage
            supabase.storage.from_("orca-images").upload(
                storage_path,
                contents
            )

            # Save DB record
            JobRepository.add_image(job_id, storage_path)

            uploaded_images.append(storage_path)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )

    # -----------------------------
    # 5️⃣ Return updated status
    # -----------------------------
    updated_job = JobRepository.get_job(job_id)

    return {
        "job_id": str(job_id),
        "uploaded_count": len(uploaded_images),
        "total_images": JobRepository.count_images(job_id),
        "status": updated_job["status"],
        "message": "Images uploaded successfully"
    }
