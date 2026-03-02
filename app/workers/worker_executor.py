# app/workers/worker_executor.py
import time
from uuid import UUID
from pathlib import Path
import shutil

from app.jobs.job_manager import JobManager
from app.jobs.job_repository import JobRepository
from app.services.method1_photogrammetry.pipeline import run_photogrammetry_pipeline


class WorkerExecutor:
    """
    Executes jobs based on their method.
    Handles state transitions automatically for Method-1.
    """

    WORKSPACE_ROOT = Path("workspace")        # Base workspace folder
    UPLOADS_ROOT = Path("uploads")            # Base uploads folder

    @staticmethod
    def run_job(job_id: UUID, method: str):
        print(f"[WorkerExecutor] Started job {job_id} (method={method})")

        # -----------------------------
        # Method-1: Photogrammetry
        # -----------------------------
        if method == "method_1":
            try:
                # 1️⃣ Mark job as PROCESSING
                JobManager.mark_processing(job_id)
                print(f"[WorkerExecutor] Job {job_id} marked as PROCESSING")

                # 2️⃣ Setup workspace for this job
                job_workspace = WorkerExecutor.WORKSPACE_ROOT / str(job_id)
                colmap_dir = job_workspace / "colmap"
                sparse_dir = colmap_dir / "sparse"
                dense_dir = colmap_dir / "dense"
                workspace_images_dir = colmap_dir / "images"

                # Create directories
                job_workspace.mkdir(parents=True, exist_ok=True)
                colmap_dir.mkdir(exist_ok=True)
                sparse_dir.mkdir(parents=True, exist_ok=True)
                dense_dir.mkdir(parents=True, exist_ok=True)

                # 3️⃣ Copy uploaded images into workspace
                uploads_images_dir = WorkerExecutor.UPLOADS_ROOT / str(job_id) / "images"
                if not uploads_images_dir.exists():
                    raise FileNotFoundError(f"Uploaded images not found at {uploads_images_dir}")
                
                if workspace_images_dir.exists():
                    shutil.rmtree(workspace_images_dir)
                shutil.copytree(uploads_images_dir, workspace_images_dir)

                print(f"[WorkerExecutor] Workspace prepared at {job_workspace}")
                print(f"[WorkerExecutor] {len(list(workspace_images_dir.glob('*')))} images copied to workspace")

                # 4️⃣ Run photogrammetry pipeline
                outputs = run_photogrammetry_pipeline(job_workspace)
                print(f"[WorkerExecutor] Pipeline finished for job {job_id}")
                print(f"[WorkerExecutor] Outputs: {outputs}")

                # 5️⃣ Mark job as COMPLETED
                JobManager.mark_completed(job_id)
                print(f"[WorkerExecutor] Job {job_id} marked as COMPLETED")

            except Exception as e:
                print(f"[WorkerExecutor] Job {job_id} failed: {e}")
                JobManager.mark_failed(job_id, reason=str(e))

        # -----------------------------
        # Method-2: AI (stub)
        # -----------------------------
        elif method == "method_2":
            print(f"[WorkerExecutor] Running method_2 AI reconstruction (stub)")
            time.sleep(2)
            # run_ai_reconstruction(job_id)

        # -----------------------------
        # Other / unimplemented methods
        # -----------------------------
        else:
            print(f"[WorkerExecutor] No execution logic for method '{method}', skipping...")
            time.sleep(1)

        print(f"[WorkerExecutor] Finished job logic for {job_id}")
