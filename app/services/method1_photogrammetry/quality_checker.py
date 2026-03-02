# app/services/method1_photogrammetry/quality_checker.py

from pathlib import Path
import trimesh

def check_mesh_quality(mesh_path: Path) -> dict:
    """
    Checks the quality of a 3D mesh.

    Args:
        mesh_path (Path): Path to the final mesh (.ply)

    Returns:
        dict: Summary metrics of the mesh

    Raises:
        RuntimeError: If the mesh fails quality checks
    """
    mesh_path = Path(mesh_path)

    if not mesh_path.exists():
        raise FileNotFoundError(f"Mesh not found: {mesh_path}")

    # Load mesh
    mesh = trimesh.load_mesh(mesh_path)

    # Metrics
    num_vertices = mesh.vertices.shape[0]
    num_faces = mesh.faces.shape[0]
    is_watertight = mesh.is_watertight
    is_manifold = mesh.is_winding_consistent  # approximate manifold check

    # Thresholds (can be tuned)
    MIN_VERTICES = 1000
    MIN_FACES = 500

    # Validation
    errors = []
    if num_vertices < MIN_VERTICES:
        errors.append(f"Too few vertices: {num_vertices} < {MIN_VERTICES}")
    if num_faces < MIN_FACES:
        errors.append(f"Too few faces: {num_faces} < {MIN_FACES}")
    if not is_watertight:
        errors.append("Mesh is not watertight")
    if not is_manifold:
        errors.append("Mesh is not manifold / winding inconsistent")

    if errors:
        error_msg = "; ".join(errors)
        raise RuntimeError(f"Mesh quality check failed: {error_msg}")

    summary = {
        "vertices": num_vertices,
        "faces": num_faces,
        "watertight": is_watertight,
        "manifold": is_manifold
    }

    print(f"[QualityChecker] Mesh quality OK: {summary}")

    return summary
