import subprocess
from pathlib import Path
import shutil

# Absolute path to COLMAP executable (Windows + CUDA)
COLMAP_EXE = Path(
    r"C:\Program Files\colmap-x64-windows-cuda\bin\colmap.exe"
)


def run_colmap_sfm(images_dir: Path, workspace_dir: Path) -> Path:
    """
    Runs COLMAP sparse reconstruction (Structure-from-Motion).

    Pipeline:
    images → feature extraction → matching → sparse mapping

    Args:
        images_dir (Path): Directory containing ONLY input images
        workspace_dir (Path): Job workspace directory

    Returns:
        Path: Path to generated sparse model directory (e.g. sparse/0)
    """

    images_dir = Path(images_dir)
    workspace_dir = Path(workspace_dir)

    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    if not COLMAP_EXE.exists():
        raise FileNotFoundError(f"COLMAP executable not found: {COLMAP_EXE}")

    colmap_dir = workspace_dir / "colmap"
    database_path = colmap_dir / "database.db"
    sparse_dir = colmap_dir / "sparse"
    colmap_images_dir = colmap_dir / "images"

    # Prepare directories
    colmap_dir.mkdir(parents=True, exist_ok=True)
    sparse_dir.mkdir(parents=True, exist_ok=True)

    # Copy images into COLMAP-controlled directory
    if colmap_images_dir.exists():
        shutil.rmtree(colmap_images_dir)
    shutil.copytree(images_dir, colmap_images_dir)

    try:
        print("[COLMAP] Feature extraction (GPU)")

        subprocess.run(
            [
                str(COLMAP_EXE),
                "feature_extractor",
                "--database_path", str(database_path),
                "--image_path", str(colmap_images_dir),
                "--ImageReader.single_camera", "1",
                "--FeatureExtraction.use_gpu", "1",
            ],
            check=True,
        )

        print("[COLMAP] Feature matching (GPU)")

        subprocess.run(
            [
                str(COLMAP_EXE),
                "exhaustive_matcher",
                "--database_path", str(database_path),
                "--FeatureMatching.use_gpu", "1",
            ],
            check=True,
        )

        print("[COLMAP] Sparse mapping")

        subprocess.run(
            [
                str(COLMAP_EXE),
                "mapper",
                "--database_path", str(database_path),
                "--image_path", str(colmap_images_dir),
                "--output_path", str(sparse_dir),
            ],
            check=True,
        )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"COLMAP failed: {e}")

    # COLMAP outputs models as sparse/0, sparse/1, ...
    model_dirs = sorted(p for p in sparse_dir.iterdir() if p.is_dir())

    if not model_dirs:
        raise RuntimeError("COLMAP completed but no sparse model was generated")

    print(f"[COLMAP] Sparse model generated at: {model_dirs[0]}")

    return model_dirs[0]
