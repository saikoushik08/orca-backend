# app/workers/worker_executor.py
import time
import shutil
from uuid import UUID
from pathlib import Path

from app.jobs.job_manager import JobManager
from app.services.method1_photogrammetry.pipeline import run_photogrammetry_pipeline


class WorkerExecutor:
    """
    Executes jobs based on their method.
    Handles state transitions automatically for Method-1.
    """

    WORKSPACE_ROOT = Path("workspace")
    UPLOADS_ROOT = Path("uploads")
    OUTPUTS_ROOT = Path("outputs")

    @staticmethod
    def run_job(job_id: UUID, method: str):
        print(f"[WorkerExecutor] Started job {job_id} (method={method})")

        if method == "method_1":
            try:
                # 1️⃣ Mark job as PROCESSING
                JobManager.mark_processing(job_id)
                print(f"[WorkerExecutor] Job {job_id} marked as PROCESSING")

                # 2️⃣ Resolve paths
                job_id_str = str(job_id)
                uploads_images_dir = WorkerExecutor.UPLOADS_ROOT / job_id_str / "images"
                job_workspace = WorkerExecutor.WORKSPACE_ROOT / job_id_str
                outputs_dir = WorkerExecutor.OUTPUTS_ROOT / job_id_str

                colmap_dir = job_workspace / "colmap"
                sparse_dir = colmap_dir / "sparse"
                dense_dir = colmap_dir / "dense"
                workspace_images_dir = colmap_dir / "images"

                # 3️⃣ Validate uploaded images exist
                if not uploads_images_dir.exists():
                    raise FileNotFoundError(
                        f"Uploaded images directory not found: {uploads_images_dir}"
                    )

                image_files = [p for p in uploads_images_dir.iterdir() if p.is_file()]
                if not image_files:
                    raise FileNotFoundError(
                        f"No uploaded images found in: {uploads_images_dir}"
                    )

                # 4️⃣ Prepare workspace + outputs
                job_workspace.mkdir(parents=True, exist_ok=True)
                outputs_dir.mkdir(parents=True, exist_ok=True)
                colmap_dir.mkdir(parents=True, exist_ok=True)
                sparse_dir.mkdir(parents=True, exist_ok=True)
                dense_dir.mkdir(parents=True, exist_ok=True)

                # 5️⃣ Copy uploaded images into workspace
                if workspace_images_dir.exists():
                    shutil.rmtree(workspace_images_dir)
                shutil.copytree(uploads_images_dir, workspace_images_dir)

                copied_images = [p for p in workspace_images_dir.iterdir() if p.is_file()]

                print(f"[WorkerExecutor] Workspace prepared at {job_workspace}")
                print(f"[WorkerExecutor] {len(copied_images)} images copied to workspace")

                # 6️⃣ Run photogrammetry pipeline
                outputs = run_photogrammetry_pipeline(job_workspace)
                print(f"[WorkerExecutor] Pipeline finished for job {job_id}")
                print(f"[WorkerExecutor] Outputs: {outputs}")

                # 7️⃣ Copy key final outputs into outputs/<job_id>/
                if isinstance(outputs, dict):
                    final_mesh = outputs.get("final_mesh")
                    dense_mesh = outputs.get("dense_mesh")
                    sparse_model = outputs.get("sparse_model")

                    if final_mesh and Path(final_mesh).exists():
                        shutil.copy2(final_mesh, outputs_dir / Path(final_mesh).name)

                    if dense_mesh and Path(dense_mesh).exists():
                        shutil.copy2(dense_mesh, outputs_dir / Path(dense_mesh).name)

                    if sparse_model and Path(sparse_model).exists():
                        sparse_export_dir = outputs_dir / "sparse_model"
                        if sparse_export_dir.exists():
                            shutil.rmtree(sparse_export_dir)
                        shutil.copytree(sparse_model, sparse_export_dir)

                # 8️⃣ Mark job as COMPLETED
                JobManager.mark_completed(job_id)
                print(f"[WorkerExecutor] Job {job_id} marked as COMPLETED")

            except Exception as e:
                print(f"[WorkerExecutor] Job {job_id} failed: {e}")
                try:
                    JobManager.mark_failed(job_id, reason=str(e))
                except Exception as mark_error:
                    print(
                        f"[WorkerExecutor] Failed to mark job {job_id} as FAILED: {mark_error}"
                    )

        elif method == "method_2":
            print(f"[WorkerExecutor] Running method_2 AI reconstruction (stub)")
            time.sleep(2)

        else:
            print(f"[WorkerExecutor] No execution logic for method '{method}', skipping...")
            time.sleep(1)

        print(f"[WorkerExecutor] Finished job logic for {job_id}")