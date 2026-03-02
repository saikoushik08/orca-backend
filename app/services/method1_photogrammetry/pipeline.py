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

    # ---- Safety checks ----
    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    # ---- Create required directories ----
    colmap_dir.mkdir(exist_ok=True)
    sparse_root.mkdir(parents=True, exist_ok=True)

    # ---- Step 1: Sparse reconstruction (SfM) ----
    sparse_model_dir = run_colmap_sfm(
        images_dir=images_dir,
        workspace_dir=workspace_dir
    )

    # ---- Step 2: Dense reconstruction ----
    dense_mesh_path = run_dense_reconstruction(
        sparse_model_dir=sparse_model_dir,
        workspace_dir=workspace_dir
    )

    # ---- Step 3: Mesh building ----
    final_mesh_path = build_mesh(dense_mesh_path, workspace_dir)
    
    # ---- Step 4: Quality check ----
    mesh_metrics = check_mesh_quality(final_mesh_path)

    return {
        "images_dir": images_dir,
        "sparse_model": sparse_model_dir,
        "dense_mesh": dense_mesh_path,
        "final_mesh": final_mesh_path,
        "mesh_metrics": mesh_metrics
    }
