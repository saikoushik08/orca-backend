# test_pipeline.py

import shutil
from uuid import uuid4
from pathlib import Path

from app.jobs.job_repository import JobRepository
from app.jobs.job_manager import JobManager
from app.workers.local_worker import LocalWorker
from app.jobs.job_states import JobStatus

# -----------------------------
# CONFIG
# -----------------------------
UPLOADS_DIR = Path(
    r"C:\Users\user0810\OneDrive\Documents\B.tech+M.tech--k\MAJOR-PROJECT\orca-backend\uploads"
)
WORKSPACE_DIR = Path("workspace")  # default workspace

# -----------------------------
# 1️⃣ Create a job
# -----------------------------
job_id = uuid4()
method = "method_1"

job = JobRepository.create_job(job_id, method)
print(f"[Test] Created job {job_id} with method {method}")

# -----------------------------
# 2️⃣ Mark job as PENDING
# -----------------------------
JobManager.start_job(job_id)
print(f"[Test] Job {job_id} marked as PENDING")

# -----------------------------
# 3️⃣ Copy images to workspace (COLMAP expects images here)
# -----------------------------
workspace_images_dir = WORKSPACE_DIR / str(job_id) / "images"
workspace_images_dir.mkdir(parents=True, exist_ok=True)

# Copy all images from your fixed uploads folder to the workspace
for img_file in UPLOADS_DIR.iterdir():
    if img_file.is_file():
        shutil.copy(img_file, workspace_images_dir)

print(f"[Test] Copied {len(list(UPLOADS_DIR.iterdir()))} images to workspace")

# -----------------------------
# 4️⃣ Dispatch job to LocalWorker
# -----------------------------
LocalWorker.execute(job_id)
print(f"[Test] Job execution finished")

# -----------------------------
# 5️⃣ Check outputs
# -----------------------------
dense_mesh_path = WORKSPACE_DIR / str(job_id) / "colmap" / "dense" / "meshed-poisson.ply"
final_mesh_path = WORKSPACE_DIR / str(job_id) / "final_mesh.ply"

print(f"[Test] Dense mesh path: {dense_mesh_path}")
print(f"[Test] Final processed mesh: {final_mesh_path}")

# -----------------------------
# 6️⃣ Job status
# -----------------------------
job_after = JobRepository.get_job(job_id)
print(f"[Test] Job status after execution: {job_after['status']}")
