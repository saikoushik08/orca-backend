from pathlib import Path
import numpy as np
from PIL import Image
import open3d as o3d


ROOT = Path("data/test_object1")
SPARSE_TXT = ROOT / "sparse_txt"
MASK_DIR = ROOT / "masks"
OUT_PLY = ROOT / "sparse_object_only.ply"


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

        # assume SIMPLE_RADIAL / PINHOLE-ish first params fx fy cx cy or f cx cy
        if model in ["SIMPLE_PINHOLE", "SIMPLE_RADIAL", "RADIAL"]:
            f, cx, cy = params[:3]
            fx = fy = f
        elif model in ["PINHOLE", "OPENCV", "OPENCV_FISHEYE", "FULL_OPENCV"]:
            fx, fy, cx, cy = params[:4]
        else:
            # fallback
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

        i += 2  # skip 2D points line
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


def main():
    cameras = load_cameras(SPARSE_TXT / "cameras.txt")
    images = load_images(SPARSE_TXT / "images.txt")
    masks = load_masks(MASK_DIR)

    kept_points = []
    total = 0
    kept = 0

    for line in (SPARSE_TXT / "points3D.txt").read_text().splitlines():
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        xyz = np.array(list(map(float, parts[1:4])))
        track = parts[8:]  # IMAGE_ID, POINT2D_IDX repeated

        total += 1
        votes = 0
        valid_obs = 0

        for j in range(0, len(track), 2):
            image_id = int(track[j])
            if image_id not in images:
                continue

            img = images[image_id]
            cam = cameras[img["cam_id"]]
            proj = project_point(xyz, img, cam)
            if proj is None:
                continue

            u, v = proj
            mask_name = img["name"].lower()
            if mask_name not in masks:
                # try png if image is jpg
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
                valid_obs += 1
                if mask[vi, ui] > 127:
                    votes += 1

        if valid_obs > 0 and votes / valid_obs >= 0.5:
            kept_points.append(xyz)
            kept += 1

    print(f"Total sparse points: {total}")
    print(f"Kept object points: {kept}")

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.array(kept_points))
    o3d.io.write_point_cloud(str(OUT_PLY), pcd)
    print(f"Saved: {OUT_PLY}")


if __name__ == "__main__":
    main()