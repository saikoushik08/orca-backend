import subprocess
from pathlib import Path


def run_dense_reconstruction(
    sparse_model_dir: Path,
    workspace_dir: Path
) -> Path:
    """
    Runs COLMAP dense reconstruction pipeline.

    Args:
        sparse_model_dir (Path): Path to sparse model (e.g., colmap/sparse/0)
        workspace_dir (Path): Job working directory

    Returns:
        Path: Path to final dense mesh (.ply)
    """

    sparse_model_dir = Path(sparse_model_dir)
    workspace_dir = Path(workspace_dir)

    if not sparse_model_dir.exists():
        raise FileNotFoundError(f"Sparse model not found: {sparse_model_dir}")

    colmap_dir = workspace_dir / "colmap"
    images_dir = colmap_dir / "images"
    dense_dir = colmap_dir / "dense"

    if not images_dir.exists():
        raise FileNotFoundError("COLMAP images directory not found")

    dense_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Undistort images
        subprocess.run(
            [
                "colmap", "image_undistorter",
                "--image_path", str(images_dir),
                "--input_path", str(sparse_model_dir),
                "--output_path", str(dense_dir),
                "--output_type", "COLMAP"
            ],
            check=True
        )

        # Step 2: Dense stereo matching
        subprocess.run(
            [
                "colmap", "patch_match_stereo",
                "--workspace_path", str(dense_dir),
                "--workspace_format", "COLMAP",
                "--PatchMatchStereo.geom_consistency", "true"
            ],
            check=True
        )

        # Step 3: Fuse depth maps into dense point cloud
        fused_ply = dense_dir / "fused.ply"
        subprocess.run(
            [
                "colmap", "stereo_fusion",
                "--workspace_path", str(dense_dir),
                "--workspace_format", "COLMAP",
                "--input_type", "geometric",
                "--output_path", str(fused_ply)
            ],
            check=True
        )

        # Step 4: Poisson mesh reconstruction
        meshed_ply = dense_dir / "meshed-poisson.ply"
        subprocess.run(
            [
                "colmap", "poisson_mesher",
                "--input_path", str(fused_ply),
                "--output_path", str(meshed_ply)
            ],
            check=True
        )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Dense reconstruction failed: {e}")

    if not meshed_ply.exists():
        raise RuntimeError("Dense mesh was not generated")

    return meshed_ply
