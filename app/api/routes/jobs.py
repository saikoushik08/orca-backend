from fastapi import APIRouter, HTTPException, Query
from uuid import uuid4, UUID

from app.jobs.job_manager import JobManager
from app.jobs.job_repository import JobRepository
from app.jobs.job_states import JobStatus
from app.workers.task_dispatcher import TaskDispatcher

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

MIN_IMAGES_REQUIRED = 5


# -----------------------------
# CREATE NEW JOB
# -----------------------------
@router.post("/")
def create_job(
    method: str = Query(
        default="method_1",
        description="Reconstruction method"
    )
):
    job_id = uuid4()

    JobRepository.create_job(job_id, method)

    return {
        "job_id": str(job_id),
        "method": method,
        "status": JobStatus.CREATED.value,
        "message": "Job created successfully"
    }


# -----------------------------
# GET JOB STATUS
# -----------------------------
@router.get("/{job_id}")
def get_job_status(job_id: UUID):
    job = JobRepository.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job["job_id"],
        "method": job["method"],
        "status": job["status"],
        "created_at": job.get("created_at")
    }


# -----------------------------
# UPDATE JOB STATUS (ADMIN / WORKER)
# SAFE: ROUTED THROUGH JobManager ONLY
# -----------------------------
@router.put("/{job_id}/status")
def update_job_status(
    job_id: UUID,
    action: str = Query(
        ...,
        description="Allowed actions: processing | completed | failed"
    )
):
    job = JobRepository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        if action == "processing":
            JobManager.mark_processing(job_id)
        elif action == "completed":
            JobManager.mark_completed(job_id)
        elif action == "failed":
            JobManager.mark_failed(job_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    updated_job = JobRepository.get_job(job_id)

    return {
        "job_id": str(job_id),
        "status": updated_job["status"],
        "message": "Job status updated successfully"
    }


# -----------------------------
# START JOB (PIPELINE TRIGGER)
# -----------------------------
@router.post("/{job_id}/start")
def start_job(job_id: UUID):
    job = JobRepository.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 1️⃣ Minimum image validation
    image_count = JobRepository.count_images(job_id)

    if image_count < MIN_IMAGES_REQUIRED:
        raise HTTPException(
            status_code=400,
            detail=(
                f"At least {MIN_IMAGES_REQUIRED} images required. "
                f"Found {image_count}"
            )
        )

    # 2️⃣ Move job → PENDING
    try:
        JobManager.start_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3️⃣ DISPATCH JOB (THIS WAS MISSING)
    TaskDispatcher.dispatch_job(job_id)

    return {
        "job_id": str(job_id),
        "status": JobStatus.PROCESSING.value,
        "images": image_count,
        "message": "Job started and dispatched to worker"
    }
