# app/services/method1_photogrammetry/mesh_builder.py

from pathlib import Path
import numpy as np
import trimesh
import open3d as o3d

# Large mesh safety thresholds
LARGE_MESH_FACE_THRESHOLD = 1_000_000
LARGE_MESH_VERTEX_THRESHOLD = 800_000


def _load_mesh_with_trimesh(mesh_path: Path):
    try:
        mesh = trimesh.load(mesh_path, force="mesh")
    except Exception as e:
        print(f"[MeshBuilder] Trimesh load failed: {e}")
        return None

    if mesh is None:
        return None

    if isinstance(mesh, trimesh.Scene):
        geometries = [g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not geometries:
            return None
        mesh = trimesh.util.concatenate(geometries)

    if not isinstance(mesh, trimesh.Trimesh):
        return None

    if mesh.vertices is None or len(mesh.vertices) == 0:
        return None

    if mesh.faces is None or len(mesh.faces) == 0:
        return None

    return mesh


def _load_mesh_with_open3d(mesh_path: Path):
    try:
        o3d_mesh = o3d.io.read_triangle_mesh(str(mesh_path))
    except Exception as e:
        print(f"[MeshBuilder] Open3D load failed: {e}")
        return None

    if o3d_mesh is None:
        return None

    if len(o3d_mesh.vertices) == 0 or len(o3d_mesh.triangles) == 0:
        return None

    try:
        mesh = trimesh.Trimesh(
            vertices=np.asarray(o3d_mesh.vertices),
            faces=np.asarray(o3d_mesh.triangles),
            process=False
        )
    except Exception as e:
        print(f"[MeshBuilder] Failed converting Open3D mesh to trimesh: {e}")
        return None

    if mesh.vertices is None or len(mesh.vertices) == 0:
        return None

    if mesh.faces is None or len(mesh.faces) == 0:
        return None

    return mesh


def _load_valid_mesh(mesh_path: Path):
    print(f"[MeshBuilder] Attempting to load mesh: {mesh_path}")

    mesh = _load_mesh_with_trimesh(mesh_path)
    if mesh is not None:
        print("[MeshBuilder] Loaded mesh with trimesh")
        return mesh

    mesh = _load_mesh_with_open3d(mesh_path)
    if mesh is not None:
        print("[MeshBuilder] Loaded mesh with Open3D fallback")
        return mesh

    return None


def _build_mesh_from_fused_pointcloud(fused_ply_path: Path):
    if not fused_ply_path.exists():
        return None

    print(f"[MeshBuilder] Falling back to fused point cloud: {fused_ply_path}")

    try:
        pcd = o3d.io.read_point_cloud(str(fused_ply_path))
    except Exception as e:
        print(f"[MeshBuilder] Failed to load fused point cloud: {e}")
        return None

    if pcd is None or len(pcd.points) == 0:
        print("[MeshBuilder] Fused point cloud is empty")
        return None

    try:
        pcd.estimate_normals()
        distances = pcd.compute_nearest_neighbor_distance()
        if not distances:
            print("[MeshBuilder] Could not compute neighbor distances")
            return None

        avg_dist = float(sum(distances) / len(distances))
        radius = max(avg_dist * 3.0, 1e-6)

        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
            pcd,
            o3d.utility.DoubleVector([radius, radius * 2.0])
        )

        if len(mesh.vertices) == 0 or len(mesh.triangles) == 0:
            print("[MeshBuilder] Ball pivoting produced an empty mesh")
            return None

        tri_mesh = trimesh.Trimesh(
            vertices=np.asarray(mesh.vertices),
            faces=np.asarray(mesh.triangles),
            process=False
        )

        if len(tri_mesh.vertices) == 0 or len(tri_mesh.faces) == 0:
            return None

        print("[MeshBuilder] Built mesh from fused point cloud fallback")
        return tri_mesh

    except Exception as e:
        print(f"[MeshBuilder] Failed to build mesh from fused point cloud: {e}")
        return None


def _is_large_mesh(mesh: trimesh.Trimesh) -> bool:
    return (
        len(mesh.faces) >= LARGE_MESH_FACE_THRESHOLD
        or len(mesh.vertices) >= LARGE_MESH_VERTEX_THRESHOLD
    )


def _keep_largest_component(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    try:
        parts = mesh.split(only_watertight=False)
    except Exception as e:
        print(f"[MeshBuilder] Component split failed: {e}")
        return mesh

    if not parts:
        return mesh

    parts = [p for p in parts if len(p.vertices) > 0 and len(p.faces) > 0]
    if not parts:
        return mesh

    largest = max(parts, key=lambda m: len(m.faces))
    print(
        f"[MeshBuilder] Kept largest component: "
        f"{len(largest.vertices)} vertices, {len(largest.faces)} faces "
        f"(from {len(parts)} components)"
    )
    return largest


def _remove_small_components(mesh: trimesh.Trimesh, min_faces: int = 300) -> trimesh.Trimesh:
    try:
        parts = mesh.split(only_watertight=False)
    except Exception as e:
        print(f"[MeshBuilder] Small-component removal split failed: {e}")
        return mesh

    if not parts:
        return mesh

    kept = [p for p in parts if len(p.faces) >= min_faces]
    if not kept:
        print("[MeshBuilder] No components met threshold, keeping original mesh")
        return mesh

    cleaned = trimesh.util.concatenate(kept)
    print(
        f"[MeshBuilder] Removed small components: kept {len(kept)} / {len(parts)} components"
    )
    return cleaned


def _smooth_with_open3d(mesh: trimesh.Trimesh, iterations: int = 5) -> trimesh.Trimesh:
    try:
        o3d_mesh = o3d.geometry.TriangleMesh()
        o3d_mesh.vertices = o3d.utility.Vector3dVector(np.asarray(mesh.vertices))
        o3d_mesh.triangles = o3d.utility.Vector3iVector(np.asarray(mesh.faces))
        o3d_mesh.compute_vertex_normals()

        o3d_mesh = o3d_mesh.filter_smooth_taubin(
            number_of_iterations=iterations
        )
        o3d_mesh.compute_vertex_normals()

        smoothed = trimesh.Trimesh(
            vertices=np.asarray(o3d_mesh.vertices),
            faces=np.asarray(o3d_mesh.triangles),
            process=False
        )

        if len(smoothed.vertices) == 0 or len(smoothed.faces) == 0:
            return mesh

        print(f"[MeshBuilder] Applied Taubin smoothing ({iterations} iterations)")
        return smoothed

    except Exception as e:
        print(f"[MeshBuilder] Smoothing skipped: {e}")
        return mesh


def build_mesh(dense_mesh_path: Path, output_dir: Path) -> Path:
    """
    Processes the dense mesh output from COLMAP and generates a final mesh.

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

    mesh = _load_valid_mesh(dense_mesh_path)

    if mesh is None:
        fused_ply_path = dense_mesh_path.parent / "fused.ply"
        mesh = _build_mesh_from_fused_pointcloud(fused_ply_path)

    if mesh is None:
        raise RuntimeError("Could not load a valid mesh from dense mesh or fused point cloud")

    if len(mesh.vertices) == 0:
        raise RuntimeError("Mesh has no vertices")

    if len(mesh.faces) == 0:
        raise RuntimeError("Mesh has no faces")

    print(
        f"[MeshBuilder] Loaded mesh with "
        f"{len(mesh.vertices)} vertices and {len(mesh.faces)} faces"
    )

    # Basic cleanup only
    for fn_name in [
        "remove_degenerate_faces",
        "remove_duplicate_faces",
        "remove_unreferenced_vertices",
        "remove_infinite_values",
    ]:
        try:
            getattr(mesh, fn_name)()
        except Exception as e:
            print(f"[MeshBuilder] {fn_name} skipped: {e}")

    # Large mesh guard: avoid RAM-heavy operations
    if _is_large_mesh(mesh):
        print(
            "[MeshBuilder] Large mesh detected. "
            "Skipping component splitting, smoothing, and simplification."
        )
    else:
        # Remove tiny floating fragments, then keep the main object
        try:
            mesh = _remove_small_components(mesh, min_faces=300)
        except Exception as e:
            print(f"[MeshBuilder] Small component removal skipped: {e}")

        try:
            mesh = _keep_largest_component(mesh)
        except Exception as e:
            print(f"[MeshBuilder] Largest component selection skipped: {e}")

        # Light smoothing to reduce rough noisy shell
        try:
            mesh = _smooth_with_open3d(mesh, iterations=5)
        except Exception as e:
            print(f"[MeshBuilder] Smoothing stage skipped: {e}")

        # Simplify only if mesh is moderately large
        face_count = len(mesh.faces)
        if 20_000 < face_count < LARGE_MESH_FACE_THRESHOLD:
            target_faces = max(8000, int(face_count * 0.6))
            try:
                mesh = mesh.simplify_quadric_decimation(target_faces)
                print(f"[MeshBuilder] Simplified mesh to ~{target_faces} faces")
            except Exception as e:
                print(f"[MeshBuilder] Simplification skipped: {e}")

    # Final validation
    if mesh.vertices is None or len(mesh.vertices) == 0:
        raise RuntimeError("Processed mesh has no vertices")

    if mesh.faces is None or len(mesh.faces) == 0:
        raise RuntimeError("Processed mesh has no faces")

    final_mesh_path = output_dir / "final_mesh.ply"
    mesh.export(final_mesh_path)

    if not final_mesh_path.exists():
        raise RuntimeError("Final mesh export failed")

    print(
        f"[MeshBuilder] Final mesh saved at: {final_mesh_path} "
        f"with {len(mesh.vertices)} vertices and {len(mesh.faces)} faces"
    )

    return final_mesh_path