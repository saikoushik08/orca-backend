# test_dispatch.py

from uuid import uuid4
from app.jobs.job_repository import JobRepository
from app.jobs.job_manager import JobManager
from app.jobs.job_states import JobStatus
from app.workers.task_dispatcher import TaskDispatcher

# Number of dummy images to simulate
NUM_IMAGES = 5


def main():
    # 1️⃣ Create a new job
    job_id = uuid4()
    JobRepository.create_job(job_id, method="method_1")
    print(f"Job created: {job_id} (status={JobStatus.CREATED.value})")

    # 2️⃣ Add dummy images
    for i in range(NUM_IMAGES):
        img_path = f"{job_id}/image_{i+1}.jpg"
        JobRepository.add_image(job_id, img_path)
    print(f"{NUM_IMAGES} images added to job {job_id}")

    # 3️⃣ Start the job
    try:
        JobManager.start_job(job_id)
        print(f"Job {job_id} started successfully (status=pending)")
    except ValueError as e:
        print(f"Failed to start job {job_id}: {e}")
        return

    # 4️⃣ Dispatch job
    try:
        TaskDispatcher.dispatch_job(job_id)
    except Exception as e:
        print(f"Dispatch failed: {e}")

    # 5️⃣ Final status
    final_job = JobRepository.get_job(job_id)
    print(f"Final status of job {job_id}: {final_job['status']}")


if __name__ == "__main__":
    main()
