# test_pipeline.py

import shutil
from uuid import uuid4
from pathlib import Path

from app.jobs.job_repository import JobRepository
from app.jobs.job_manager import JobManager
from app.workers.local_worker import LocalWorker

# -----------------------------
# CONFIG
# -----------------------------
# Put your source test images inside:
# K:\ORCA\orca-backend\uploads_test_images
SOURCE_TEST_IMAGES_DIR = Path("uploads_test_images")

UPLOADS_ROOT = Path("uploads")
WORKSPACE_ROOT = Path("workspace")
OUTPUTS_ROOT = Path("outputs")

# -----------------------------
# 1️⃣ Validate source images
# -----------------------------
if not SOURCE_TEST_IMAGES_DIR.exists():
    raise FileNotFoundError(
        f"[Test] Source test images folder not found: {SOURCE_TEST_IMAGES_DIR.resolve()}"
    )

source_images = [p for p in SOURCE_TEST_IMAGES_DIR.iterdir() if p.is_file()]
if len(source_images) < 5:
    raise RuntimeError(
        f"[Test] At least 5 test images are required. Found: {len(source_images)}"
    )

print(f"[Test] Found {len(source_images)} source test images")

# -----------------------------
# 2️⃣ Create a job
# -----------------------------
job_id = uuid4()
method = "method_1"

JobRepository.create_job(job_id, method)
print(f"[Test] Created job {job_id} with method {method}")

# -----------------------------
# 3️⃣ Simulate real upload flow
#    Copy images into uploads/<job_id>/images/
# -----------------------------
job_upload_dir = UPLOADS_ROOT / str(job_id) / "images"
job_upload_dir.mkdir(parents=True, exist_ok=True)

for img_file in source_images:
    shutil.copy2(img_file, job_upload_dir / img_file.name)

copied_images = [p for p in job_upload_dir.iterdir() if p.is_file()]
print(f"[Test] Copied {len(copied_images)} images to {job_upload_dir}")

# Also register image metadata in DB so count_images() works
for img_file in copied_images:
    storage_path = f"{job_id}/{img_file.name}"
    JobRepository.add_image(job_id, storage_path)

print(f"[Test] Registered {len(copied_images)} images in DB")

# -----------------------------
# 4️⃣ Mark job as PENDING
# -----------------------------
JobManager.start_job(job_id)
print(f"[Test] Job {job_id} marked as PENDING")

# -----------------------------
# 5️⃣ Execute through LocalWorker
# -----------------------------
LocalWorker.execute(job_id)
print(f"[Test] Job execution finished")

# -----------------------------
# 6️⃣ Check outputs
# -----------------------------
job_workspace = WORKSPACE_ROOT / str(job_id)
job_outputs = OUTPUTS_ROOT / str(job_id)

dense_mesh_path = job_workspace / "colmap" / "dense" / "meshed-poisson.ply"
final_mesh_path = job_workspace / "final_mesh.ply"
copied_output_mesh = job_outputs / "final_mesh.ply"

print(f"[Test] Dense mesh path: {dense_mesh_path}")
print(f"[Test] Dense mesh exists: {dense_mesh_path.exists()}")

print(f"[Test] Final processed mesh path: {final_mesh_path}")
print(f"[Test] Final processed mesh exists: {final_mesh_path.exists()}")

print(f"[Test] Output exported mesh path: {copied_output_mesh}")
print(f"[Test] Output exported mesh exists: {copied_output_mesh.exists()}")

# -----------------------------
# 7️⃣ Final job status
# -----------------------------
job_after = JobRepository.get_job(job_id)
print(f"[Test] Job status after execution: {job_after['status']}")

# -----------------------------
# 8️⃣ Summary
# -----------------------------
if final_mesh_path.exists() and job_after["status"] == "completed":
    print("[Test] SUCCESS: Method-1 pipeline completed successfully")
else:
    print("[Test] WARNING: Pipeline did not complete successfully")