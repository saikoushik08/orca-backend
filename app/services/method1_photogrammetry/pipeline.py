# app/services/method1_photogrammetry/pipeline.py
from pathlib import Path

from app.services.method1_photogrammetry.colmap_runner import run_colmap_sfm
from app.services.method1_photogrammetry.dense_reconstruction import run_dense_reconstruction
from app.services.method1_photogrammetry.mesh_builder import build_mesh
from app.services.method1_photogrammetry.quality_checker import check_mesh_quality


def run_photogrammetry_pipeline(workspace_dir: Path) -> dict:
    """
    Full photogrammetry pipeline for Method-1:
    images -> sparse reconstruction -> dense reconstruction -> mesh -> quality check

    Args:
        workspace_dir (Path): Job working directory (workspace/{job_id})

    Returns:
        dict: Paths to key outputs and mesh metrics
    """
    workspace_dir = Path(workspace_dir)

    # ---- Define COLMAP directories ----
    colmap_dir = workspace_dir / "colmap"
    images_dir = colmap_dir / "images"
    sparse_root = colmap_dir / "sparse"
    dense_dir = colmap_dir / "dense"

    # ---- Safety checks ----
    if not workspace_dir.exists():
        raise FileNotFoundError(f"Workspace directory not found: {workspace_dir}")

    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    image_files = [p for p in images_dir.iterdir() if p.is_file()]
    if not image_files:
        raise FileNotFoundError(f"No images found in: {images_dir}")

    # ---- Create required directories ----
    colmap_dir.mkdir(parents=True, exist_ok=True)
    sparse_root.mkdir(parents=True, exist_ok=True)
    dense_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Pipeline] Starting Method-1 photogrammetry pipeline in: {workspace_dir}")
    print(f"[Pipeline] Found {len(image_files)} input images")

    # ---- Step 1: Sparse reconstruction (SfM) ----
    print("[Pipeline] Step 1/4 - Sparse reconstruction")
    sparse_model_dir = run_colmap_sfm(
        images_dir=images_dir,
        workspace_dir=workspace_dir
    )

    # ---- Step 2: Dense reconstruction ----
    print("[Pipeline] Step 2/4 - Dense reconstruction")
    dense_mesh_path = run_dense_reconstruction(
        sparse_model_dir=sparse_model_dir,
        workspace_dir=workspace_dir
    )

    # ---- Step 3: Mesh building ----
    print("[Pipeline] Step 3/4 - Mesh post-processing")
    final_mesh_path = build_mesh(dense_mesh_path, workspace_dir)

    if not Path(final_mesh_path).exists():
        raise RuntimeError(f"Final mesh was not generated: {final_mesh_path}")

    # ---- Step 4: Quality check ----
    print("[Pipeline] Step 4/4 - Mesh quality check")
    mesh_metrics = check_mesh_quality(final_mesh_path)

    outputs = {
        "workspace_dir": workspace_dir,
        "images_dir": images_dir,
        "sparse_model": sparse_model_dir,
        "dense_mesh": dense_mesh_path,
        "final_mesh": final_mesh_path,
        "mesh_metrics": mesh_metrics,
    }

    print(f"[Pipeline] Method-1 completed successfully")
    print(f"[Pipeline] Final mesh: {final_mesh_path}")

    return outputs