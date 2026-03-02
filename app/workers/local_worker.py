# app/workers/local_worker.py

from uuid import UUID
from app.jobs.job_manager import JobManager
from app.jobs.job_repository import JobRepository
from app.workers.worker_executor import WorkerExecutor
from app.jobs.job_states import JobStatus


class LocalWorker:
    """
    Executes jobs locally using WorkerExecutor.

    Responsibilities:
    1️⃣ Ensure job is in PENDING state before execution
    2️⃣ Trigger WorkerExecutor (which handles PROCESSING → COMPLETED/FAILED)
    3️⃣ Log progress
    """

    @staticmethod
    def execute(job_id: UUID):
        # 1️⃣ Fetch job
        job = JobRepository.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        current_status = JobStatus(job["status"])

        # 2️⃣ Ensure job is PENDING before execution
        if current_status != JobStatus.PENDING:
            raise ValueError(
                f"Cannot execute job {job_id} from state '{current_status.value}'"
            )

        # 3️⃣ Delegate actual execution to WorkerExecutor
        method = job["method"]
        print(f"[LocalWorker] Dispatching job {job_id} (method={method}) to WorkerExecutor")
        WorkerExecutor.run_job(job_id, method)

        print(f"[LocalWorker] Job {job_id} execution finished")
