import subprocess
from pathlib import Path

# Keep COLMAP invocation consistent with colmap_runner.py
COLMAP_EXE = Path(
    r"C:\Program Files\colmap-x64-windows-cuda\bin\colmap.exe"
)

# Debug / test settings
DEBUG_UNDISTORT_MAX_IMAGE_SIZE = 1600
DEBUG_PATCHMATCH_WINDOW_RADIUS = 3
DEBUG_PATCHMATCH_NUM_ITERATIONS = 3
DEBUG_STEREO_FUSION_MAX_IMAGE_SIZE = 1600


def run_dense_reconstruction(
    sparse_model_dir: Path,
    workspace_dir: Path
) -> Path:
    """
    Runs a lighter COLMAP dense reconstruction pipeline for testing.

    Args:
        sparse_model_dir (Path): Path to sparse model (e.g. colmap/sparse/0)
        workspace_dir (Path): Job working directory

    Returns:
        Path: Path to final dense mesh (.ply)
    """

    sparse_model_dir = Path(sparse_model_dir)
    workspace_dir = Path(workspace_dir)

    if not sparse_model_dir.exists():
        raise FileNotFoundError(f"Sparse model not found: {sparse_model_dir}")

    if not COLMAP_EXE.exists():
        raise FileNotFoundError(f"COLMAP executable not found: {COLMAP_EXE}")

    colmap_dir = workspace_dir / "colmap"
    images_dir = colmap_dir / "images"
    dense_dir = colmap_dir / "dense"

    if not images_dir.exists():
        raise FileNotFoundError(f"COLMAP images directory not found: {images_dir}")

    dense_dir.mkdir(parents=True, exist_ok=True)

    fused_ply = dense_dir / "fused.ply"
    meshed_ply = dense_dir / "meshed-poisson.ply"

    try:
        print("[COLMAP] Image undistortion (debug mode)")
        subprocess.run(
            [
                str(COLMAP_EXE),
                "image_undistorter",
                "--image_path", str(images_dir),
                "--input_path", str(sparse_model_dir),
                "--output_path", str(dense_dir),
                "--output_type", "COLMAP",
                "--max_image_size", str(DEBUG_UNDISTORT_MAX_IMAGE_SIZE),
            ],
            check=True,
        )

        print("[COLMAP] Patch match stereo (debug mode)")
        subprocess.run(
            [
                str(COLMAP_EXE),
                "patch_match_stereo",
                "--workspace_path", str(dense_dir),
                "--workspace_format", "COLMAP",
                "--PatchMatchStereo.geom_consistency", "false",
                "--PatchMatchStereo.window_radius", str(DEBUG_PATCHMATCH_WINDOW_RADIUS),
                "--PatchMatchStereo.num_iterations", str(DEBUG_PATCHMATCH_NUM_ITERATIONS),
            ],
            check=True,
        )

        print("[COLMAP] Stereo fusion (debug mode)")
        subprocess.run(
            [
                str(COLMAP_EXE),
                "stereo_fusion",
                "--workspace_path", str(dense_dir),
                "--workspace_format", "COLMAP",
                "--input_type", "photometric",
                "--output_path", str(fused_ply),
                "--StereoFusion.max_image_size", str(DEBUG_STEREO_FUSION_MAX_IMAGE_SIZE),
            ],
            check=True,
        )

        if not fused_ply.exists():
            raise RuntimeError("Dense point cloud was not generated")

        print("[COLMAP] Poisson meshing")
        subprocess.run(
            [
                str(COLMAP_EXE),
                "poisson_mesher",
                "--input_path", str(fused_ply),
                "--output_path", str(meshed_ply),
            ],
            check=True,
        )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Dense reconstruction failed: {e}")

    if not meshed_ply.exists():
        raise RuntimeError("Dense mesh was not generated")

    return meshed_ply