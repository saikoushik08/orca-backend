# app/jobs/job_manager.py

from uuid import UUID

from app.jobs.job_states import (
    JobStatus,
    UPLOAD_ALLOWED_STATES,
    JOB_START_ALLOWED_STATES,
    TERMINAL_STATES,
)
from app.jobs.job_repository import JobRepository


class JobManager:
    """
    Central authority for job lifecycle management.
    All state transitions MUST go through this class.
    """

    # -----------------------------
    # INTERNAL HELPERS
    # -----------------------------

    @staticmethod
    def _get_job_or_fail(job_id: UUID) -> dict:
        job = JobRepository.get_job(job_id)
        if not job:
            raise ValueError("Job not found")
        return job

    @staticmethod
    def _ensure_not_terminal(status: JobStatus):
        if status in TERMINAL_STATES:
            raise ValueError(
                f"Job is already in terminal state '{status.value}'"
            )

    # -----------------------------
    # STATE CHECKS
    # -----------------------------

    @staticmethod
    def can_upload_images(job_id: UUID) -> bool:
        job = JobManager._get_job_or_fail(job_id)
        return JobStatus(job["status"]) in UPLOAD_ALLOWED_STATES

    @staticmethod
    def can_start_job(job_id: UUID) -> bool:
        job = JobManager._get_job_or_fail(job_id)
        return JobStatus(job["status"]) in JOB_START_ALLOWED_STATES

    # -----------------------------
    # STATE TRANSITIONS
    # -----------------------------

    @staticmethod
    def mark_uploading(job_id: UUID):
        """
        Move job to UPLOADING state when first image upload starts.
        Allowed only from CREATED.
        """
        job = JobManager._get_job_or_fail(job_id)
        current_status = JobStatus(job["status"])

        if current_status != JobStatus.CREATED:
            return  # silently ignore if already uploading

        JobRepository.update_status(job_id, JobStatus.UPLOADING)

    @staticmethod
    def start_job(job_id: UUID):
        job = JobManager._get_job_or_fail(job_id)
        current_status = JobStatus(job["status"])

        if current_status not in JOB_START_ALLOWED_STATES:
            raise ValueError(
                f"Cannot start job from state '{current_status.value}'"
            )

        JobRepository.update_status(job_id, JobStatus.PENDING)

    @staticmethod
    def mark_processing(job_id: UUID):
        job = JobManager._get_job_or_fail(job_id)
        current_status = JobStatus(job["status"])

        if current_status != JobStatus.PENDING:
            raise ValueError(
                f"Cannot mark processing from state '{current_status.value}'"
            )

        JobRepository.update_status(job_id, JobStatus.PROCESSING)

    @staticmethod
    def mark_completed(job_id: UUID):
        job = JobManager._get_job_or_fail(job_id)
        current_status = JobStatus(job["status"])

        JobManager._ensure_not_terminal(current_status)

        if current_status != JobStatus.PROCESSING:
            raise ValueError(
                f"Cannot complete job from state '{current_status.value}'"
            )

        JobRepository.update_status(job_id, JobStatus.COMPLETED)

    @staticmethod
    def mark_failed(job_id: UUID, reason: str | None = None):
        job = JobManager._get_job_or_fail(job_id)
        current_status = JobStatus(job["status"])

        JobManager._ensure_not_terminal(current_status)

        # (Optional) later store failure reason in DB
        JobRepository.update_status(job_id, JobStatus.FAILED)
