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
        RuntimeError: If the mesh is invalid or too poor to trust
    """
    mesh_path = Path(mesh_path)

    if not mesh_path.exists():
        raise FileNotFoundError(f"Mesh not found: {mesh_path}")

    mesh = trimesh.load_mesh(mesh_path)

    if mesh is None:
        raise RuntimeError("Failed to load mesh for quality check")

    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(
            [g for g in mesh.geometry.values()]
        )

    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError("Loaded object is not a valid mesh")

    if mesh.vertices is None or len(mesh.vertices) == 0:
        raise RuntimeError("Mesh has no vertices")

    if mesh.faces is None or len(mesh.faces) == 0:
        raise RuntimeError("Mesh has no faces")

    num_vertices = len(mesh.vertices)
    num_faces = len(mesh.faces)
    is_watertight = bool(mesh.is_watertight)
    is_winding_consistent = bool(mesh.is_winding_consistent)
    euler_number = int(mesh.euler_number) if hasattr(mesh, "euler_number") else None
    bounds = mesh.bounds.tolist() if hasattr(mesh, "bounds") else None
    extents = mesh.extents.tolist() if hasattr(mesh, "extents") else None

    # Keep thresholds practical for early backend testing
    MIN_VERTICES = 100
    MIN_FACES = 100

    errors = []
    warnings = []

    if num_vertices < MIN_VERTICES:
        errors.append(f"Too few vertices: {num_vertices} < {MIN_VERTICES}")

    if num_faces < MIN_FACES:
        errors.append(f"Too few faces: {num_faces} < {MIN_FACES}")

    # For early ORCA backend testing, do not hard-fail just because
    # the mesh is not watertight. Record it as a warning.
    if not is_watertight:
        warnings.append("Mesh is not watertight")

    if not is_winding_consistent:
        warnings.append("Mesh winding is inconsistent")

    if errors:
        error_msg = "; ".join(errors)
        raise RuntimeError(f"Mesh quality check failed: {error_msg}")

    summary = {
        "vertices": num_vertices,
        "faces": num_faces,
        "watertight": is_watertight,
        "winding_consistent": is_winding_consistent,
        "euler_number": euler_number,
        "bounds": bounds,
        "extents": extents,
        "warnings": warnings,
    }

    print(f"[QualityChecker] Mesh quality summary: {summary}")

    return summary