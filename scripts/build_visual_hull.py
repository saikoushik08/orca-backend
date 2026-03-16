from pathlib import Path
import numpy as np
from PIL import Image
import open3d as o3d


ROOT = Path("data/test_object1")
SPARSE_TXT = ROOT / "sparse_txt"
MASK_DIR = ROOT / "masks"
OUT_PLY = ROOT / "visual_hull.ply"


# ---------- COLMAP parsing ----------

def load_cameras(path):
    cams = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        cam_id = int(parts[0])
        model = parts[1]
        width = int(parts[2])
        height = int(parts[3])
        params = list(map(float, parts[4:]))

        if model in ["SIMPLE_PINHOLE", "SIMPLE_RADIAL", "RADIAL"]:
            f, cx, cy = params[:3]
            fx = fy = f
        elif model in ["PINHOLE", "OPENCV", "OPENCV_FISHEYE", "FULL_OPENCV"]:
            fx, fy, cx, cy = params[:4]
        else:
            fx = fy = params[0]
            cx = width / 2
            cy = height / 2

        cams[cam_id] = {
            "model": model,
            "width": width,
            "height": height,
            "fx": fx,
            "fy": fy,
            "cx": cx,
            "cy": cy,
        }
    return cams


def qvec_to_rotmat(qvec):
    qw, qx, qy, qz = qvec
    return np.array([
        [1 - 2*qy*qy - 2*qz*qz, 2*qx*qy - 2*qz*qw, 2*qx*qz + 2*qy*qw],
        [2*qx*qy + 2*qz*qw, 1 - 2*qx*qx - 2*qz*qz, 2*qy*qz - 2*qx*qw],
        [2*qx*qz - 2*qy*qw, 2*qy*qz + 2*qx*qw, 1 - 2*qx*qx - 2*qy*qy],
    ])


def load_images(path):
    imgs = {}
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        parts = line.split()
        image_id = int(parts[0])
        qvec = np.array(list(map(float, parts[1:5])))
        tvec = np.array(list(map(float, parts[5:8])))
        cam_id = int(parts[8])
        name = parts[9]

        imgs[image_id] = {
            "qvec": qvec,
            "tvec": tvec,
            "cam_id": cam_id,
            "name": name,
        }

        i += 2
    return imgs


def project_point(X, img, cam):
    R = qvec_to_rotmat(img["qvec"])
    t = img["tvec"]
    Xc = R @ X + t
    if Xc[2] <= 1e-8:
        return None

    x = Xc[0] / Xc[2]
    y = Xc[1] / Xc[2]
    u = cam["fx"] * x + cam["cx"]
    v = cam["fy"] * y + cam["cy"]
    return u, v


def load_masks(mask_dir):
    masks = {}
    for p in mask_dir.iterdir():
        if p.suffix.lower() not in [".png", ".jpg", ".jpeg"]:
            continue
        masks[p.name.lower()] = np.array(Image.open(p).convert("L"))
    return masks


# ---------- Main visual hull ----------

def main():
    cameras = load_cameras(SPARSE_TXT / "cameras.txt")
    images = load_images(SPARSE_TXT / "images.txt")
    masks = load_masks(MASK_DIR)

    # use object-only sparse points to define bbox
    pcd = o3d.io.read_point_cloud(str(ROOT / "sparse_object_only.ply"))
    pts = np.asarray(pcd.points)

    min_bound = pts.min(axis=0)
    max_bound = pts.max(axis=0)

    # add small padding
    pad = 0.05 * (max_bound - min_bound)
    min_bound -= pad
    max_bound += pad

    print("Bounding box min:", min_bound)
    print("Bounding box max:", max_bound)

    # voxel resolution
    resolution = 96
    xs = np.linspace(min_bound[0], max_bound[0], resolution)
    ys = np.linspace(min_bound[1], max_bound[1], resolution)
    zs = np.linspace(min_bound[2], max_bound[2], resolution)

    occ = np.zeros((resolution, resolution, resolution), dtype=np.uint8)

    total_voxels = resolution ** 3
    checked = 0

    image_items = list(images.items())

    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):
            for iz, z in enumerate(zs):
                X = np.array([x, y, z], dtype=np.float64)

                valid_views = 0
                inside_votes = 0

                for _, img in image_items:
                    cam = cameras[img["cam_id"]]

                    proj = project_point(X, img, cam)
                    if proj is None:
                        continue

                    u, v = proj
                    mask_name = img["name"].lower()
                    if mask_name not in masks:
                        stem = Path(mask_name).stem
                        for ext in [".png", ".jpg", ".jpeg"]:
                            alt = stem + ext
                            if alt in masks:
                                mask_name = alt
                                break

                    if mask_name not in masks:
                        continue

                    mask = masks[mask_name]
                    h, w = mask.shape[:2]
                    ui = int(round(u))
                    vi = int(round(v))

                    if 0 <= ui < w and 0 <= vi < h:
                        valid_views += 1
                        if mask[vi, ui] > 127:
                            inside_votes += 1

                # require enough support
                if valid_views >= 5 and inside_votes / valid_views >= 0.7:
                    occ[ix, iy, iz] = 1

                checked += 1
                if checked % 100000 == 0:
                    print(f"Checked {checked}/{total_voxels} voxels")

    print("Occupied voxels:", occ.sum())

    # create Open3D voxel centers point cloud
    occupied = np.argwhere(occ > 0)
    if len(occupied) == 0:
        print("No occupied voxels found. Try lowering threshold or resolution.")
        return

    points = []
    for i, j, k in occupied:
        points.append([xs[i], ys[j], zs[k]])
    points = np.array(points)

    pcd_occ = o3d.geometry.PointCloud()
    pcd_occ.points = o3d.utility.Vector3dVector(points)

    # estimate normals and mesh with alpha shape
    pcd_occ.estimate_normals()

    voxel_size = np.mean([
        (max_bound[0] - min_bound[0]) / (resolution - 1),
        (max_bound[1] - min_bound[1]) / (resolution - 1),
        (max_bound[2] - min_bound[2]) / (resolution - 1),
    ])
    alpha = voxel_size * 2.5
    print("Visual hull alpha:", alpha)

    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd_occ, alpha)
    mesh.compute_vertex_normals()

    o3d.io.write_triangle_mesh(str(OUT_PLY), mesh)
    print(f"Saved: {OUT_PLY}")


if __name__ == "__main__":
    main()