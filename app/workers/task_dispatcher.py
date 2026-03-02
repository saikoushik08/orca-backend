# app/workers/task_dispatcher.py

from uuid import UUID
from typing import Optional

from app.jobs.job_repository import JobRepository
from app.jobs.job_states import JobStatus
from app.workers.worker_executor import WorkerExecutor


class TaskDispatcher:
    """
    Responsible for dispatching PENDING jobs to workers.
    Dispatcher does NOT perform state transitions itself.
    """

    @staticmethod
    def dispatch_job(job_id: UUID):
        """
        Dispatch a single job to a worker.
        """

        # 1️⃣ Verify job exists
        job = JobRepository.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # 2️⃣ Job must be PENDING
        if job["status"] != JobStatus.PENDING.value:
            raise ValueError(
                f"Job {job_id} is not ready for dispatch "
                f"(current status: {job['status']})"
            )

        method = job.get("method", "method_1")

        # 3️⃣ Delegate execution to WorkerExecutor
        try:
            WorkerExecutor.run_job(job_id, method)
        except Exception as e:
            print(f"[TaskDispatcher] Worker failed for job {job_id}: {e}")

    @staticmethod
    def dispatch_next_pending_job() -> Optional[str]:
        """
        Find the next PENDING job and dispatch it.
        Returns the dispatched job_id as string or None if no PENDING jobs.
        """

        jobs = JobRepository.get_pending_jobs(limit=1)

        if not jobs:
            return None

        job_id = UUID(jobs[0]["job_id"])
        TaskDispatcher.dispatch_job(job_id)

        return str(job_id)
