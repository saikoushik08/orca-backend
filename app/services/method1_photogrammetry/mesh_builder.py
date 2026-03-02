# app/services/method1_photogrammetry/mesh_builder.py

from pathlib import Path
import trimesh  # Lightweight mesh library for processing

def build_mesh(dense_mesh_path: Path, output_dir: Path) -> Path:
    """
    Processes the dense mesh output from COLMAP and generates a final mesh.
    This can include cleaning, simplification, or format conversion.

    Args:
        dense_mesh_path (Path): Path to dense reconstruction mesh (meshed-poisson.ply)
        output_dir (Path): Directory to save the final mesh

    Returns:
        Path: Path to the final processed mesh (.ply)
    """
    dense_mesh_path = Path(dense_mesh_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not dense_mesh_path.exists():
        raise FileNotFoundError(f"Dense mesh not found: {dense_mesh_path}")

    # Load mesh using trimesh
    mesh = trimesh.load_mesh(dense_mesh_path)

    # Optional: remove degenerate faces / zero-area faces
    mesh.remove_degenerate_faces()
    mesh.remove_unreferenced_vertices()

    # Optional: simplify mesh to reduce size
    # e.g., keep 50% of faces (you can adjust)
    target_faces = int(mesh.faces.shape[0] * 0.5)
    mesh = mesh.simplify_quadratic_decimation(target_faces)

    # Save final mesh
    final_mesh_path = output_dir / "final_mesh.ply"
    mesh.export(final_mesh_path)

    print(f"[MeshBuilder] Final mesh saved at: {final_mesh_path}")

    return final_mesh_path
