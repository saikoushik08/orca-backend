from pathlib import Path
import numpy as np
import open3d as o3d

IN_FILE = Path("data/test_object1/sparse_object_only.ply")
OUT_NPY = Path("data/test_object1/pointr_input.npy")
OUT_PLY = Path("data/test_object1/pointr_input_normalized.ply")

TARGET_POINTS = 2048

pcd = o3d.io.read_point_cloud(str(IN_FILE))
pts = np.asarray(pcd.points)

print("Original points:", pts.shape)

# downsample if too many
if len(pts) > TARGET_POINTS:
    idx = np.random.choice(len(pts), TARGET_POINTS, replace=False)
    pts = pts[idx]
elif len(pts) < TARGET_POINTS:
    idx = np.random.choice(len(pts), TARGET_POINTS - len(pts), replace=True)
    pts = np.vstack([pts, pts[idx]])

# center
centroid = pts.mean(axis=0)
pts = pts - centroid

# scale to unit sphere
scale = np.linalg.norm(pts, axis=1).max()
pts = pts / scale

np.save(OUT_NPY, pts.astype(np.float32))

pcd_out = o3d.geometry.PointCloud()
pcd_out.points = o3d.utility.Vector3dVector(pts)
o3d.io.write_point_cloud(str(OUT_PLY), pcd_out)

print("Saved:", OUT_NPY)
print("Saved:", OUT_PLY)
print("Centroid:", centroid)
print("Scale:", scale)
print("Final shape:", pts.shape)