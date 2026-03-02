# app/jobs/job_repository.py

from typing import Optional
from uuid import UUID
from datetime import datetime

from app.storage.supabase_client import supabase
from app.jobs.job_states import JobStatus


class JobRepository:
    """
    Handles ALL database operations related to jobs and job images.
    No API or worker should talk to Supabase directly.
    """

    # -----------------------------
    # JOB OPERATIONS
    # -----------------------------

    @staticmethod
    def get_job(job_id: UUID) -> Optional[dict]:
        response = (
            supabase
            .table("jobs")
            .select("*")
            .eq("job_id", str(job_id))
            .single()
            .execute()
        )
        return response.data

    @staticmethod
    def create_job(job_id: UUID, method: str) -> dict:
        response = (
            supabase
            .table("jobs")
            .insert({
                "job_id": str(job_id),
                "method": method,
                "status": JobStatus.CREATED.value,
                "created_at": datetime.utcnow().isoformat()
            })
            .execute()
        )
        return response.data

    @staticmethod
    def update_status(job_id: UUID, next_status: JobStatus) -> dict:
        job = JobRepository.get_job(job_id)

        if not job:
            raise ValueError("Job not found")

        response = (
            supabase
            .table("jobs")
            .update({
                "status": next_status.value,
                "updated_at": datetime.utcnow().isoformat()
            })
            .eq("job_id", str(job_id))
            .execute()
        )

        return response.data

    # -----------------------------
    # IMAGE OPERATIONS
    # -----------------------------

    @staticmethod
    def count_images(job_id: UUID) -> int:
        response = (
            supabase
            .table("images")
            .select("id", count="exact")
            .eq("job_id", str(job_id))
            .execute()
        )
        return response.count or 0

    @staticmethod
    def add_image(job_id: UUID, image_path: str):
        response = (
            supabase
            .table("images")
            .insert({
                "job_id": str(job_id),
                "image_path": image_path,
                "uploaded_at": datetime.utcnow().isoformat()
            })
            .execute()
        )
        return response.data

    @staticmethod
    def list_images(job_id: UUID) -> list:
        response = (
            supabase
            .table("images")
            .select("image_path, uploaded_at")
            .eq("job_id", str(job_id))
            .execute()
        )
        return response.data or []
