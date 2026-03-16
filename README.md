# ORCA Backend

Backend engine for **ORCA (Object Reconstruction via Computational AI)** — a remote 3D object reconstruction system that combines **classical photogrammetry** and **AI-assisted geometry completion**.

ORCA is designed to reconstruct 3D objects from user-provided images, process them remotely, and generate outputs such as sparse point clouds, meshes, and refined 3D models for visualization and download.

---

## Overview

ORCA backend provides the reconstruction core for the project and supports multiple reconstruction strategies.

The system currently focuses on two main approaches:

- **Method 1 — Classical Photogrammetry**
- **Method 2 — Hybrid Sparse Reconstruction + AI Completion**

The backend is structured to support image ingestion, job execution, geometry processing, reconstruction experiments, and future web-based deployment.

---

## Key Features

- Remote image-based 3D reconstruction
- Multi-method reconstruction design
- Sparse and dense geometry workflows
- Mesh generation and refinement
- Mask-guided reconstruction support
- Hybrid AI-assisted completion pipeline
- Extensible backend service structure

---

## Reconstruction Methods

## Method 1 — Classical Photogrammetry

Method 1 is the traditional reconstruction pipeline based on photogrammetry.

### Pipeline
1. Upload object images
2. Preprocess input images
3. Extract and match features
4. Perform sparse reconstruction using **COLMAP**
5. Run dense reconstruction
6. Generate dense point cloud
7. Reconstruct mesh
8. Clean, simplify, and export 3D output

### Main Tools
- COLMAP
- OpenMVS
- Open3D
- Trimesh
- MeshLab
- Python services

### Advantages
- Strong geometric accuracy with good image coverage
- Reliable as a baseline reconstruction pipeline

### Limitations
- Dense reconstruction can be time-consuming
- Performance drops when the object has missing views, weak texture, or difficult geometry
- Final mesh quality may still require heavy cleanup

---

## Method 2 — Hybrid Sparse Reconstruction + AI Completion

Method 2 is the finalized hybrid approach for ORCA.

Instead of depending fully on dense photogrammetry, this method starts from the accurate **COLMAP sparse reconstruction** and improves the object using geometry processing, masked-image constraints, and AI-based completion.

### Core Idea
- Use **Method 1 sparse reconstruction** as the reliable geometric base
- Recover object support using classical geometry methods
- Use **masked images** to guide global shape recovery
- Push geometry-only refinement until it reaches its limit
- Use pretrained AI / 3D prior models only for the missing and incomplete parts

### Method 2 Workflow
1. Start from COLMAP sparse reconstruction
2. Export sparse point cloud
3. Filter object-only sparse geometry
4. Build coarse support mesh from sparse cloud
5. Use masked images to generate a **visual hull**
6. Fuse visual hull geometry with sparse-derived mesh
7. Refine fused support geometry using classical processing
8. Detect incomplete regions, holes, and weak surfaces
9. Apply pretrained AI / 3D completion models for refinement
10. Merge refined result into final 3D output

### Why Method 2 Exists
Method 1 gives a strong sparse base, but dense photogrammetry alone is often too slow or unstable for complex objects.  
Method 2 reduces dependence on expensive dense reconstruction and uses AI only where geometry is uncertain or missing.

### Current Status
- Sparse-geometry stage implemented and tested
- Visual-hull-based geometric support tested
- Geometry-only refinement reached its practical limit
- AI refinement stage prepared as the next enhancement step

---

## Project Structure

```text
orca-backend/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── db/
│   │   └── database.py
│   ├── jobs/
│   ├── services/
│   │   ├── method1_photogrammetry/
│   │   ├── method2_ai/
│   │   ├── method3_hybrid/
│   │   ├── storage/
│   │   ├── workers/
│   │   └── utils/
│   ├── scripts/
│   └── tests/
├── data/
├── uploads/
├── requirements.txt
├── Dockerfile
├── README.md
└── .env
```


## Installation

This section explains how to set up the ORCA backend for development and reconstruction experiments.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd orca-backend
```

2. Create a Python Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
Linux / Ubuntu
python3 -m venv venv
source venv/bin/activate
```

3. Upgrade pip
```bash
pip install --upgrade pip
```
5. Install Backend Python Dependencies
```bash
pip install -r requirements.txt
```
If needed, install the common backend and reconstruction libraries manually:
```bash
pip install fastapi uvicorn python-multipart pydantic sqlalchemy
pip install numpy scipy pillow matplotlib opencv-python
pip install open3d trimesh scikit-image scikit-learn
```
External Dependencies
The ORCA backend depends on a few external tools for reconstruction workflows.
5. Install COLMAP
COLMAP is required for sparse reconstruction and camera pose estimation.
```bash
sudo apt update
sudo apt install colmap
```
Download and install COLMAP
Add COLMAP to your system PATH
Verify installation:
```bash
colmap -h
```
6. Install FFmpeg
FFmpeg is useful when extracting frames from videos or preprocessing media inputs.
```bash
sudo apt install ffmpeg
```
Install FFmpeg
Add FFmpeg to system PATH
Verify:
```bash
ffmpeg -version
```
7. Install OpenMVS (Optional / Method 1)
OpenMVS is mainly used in the classical photogrammetry pipeline for dense reconstruction and mesh generation.
Install it separately depending on your operating system.
Install prebuilt binaries or build from source if required.

8. Install MeshLab (Optional)
MeshLab is useful for:
viewing meshes
manual cleanup
checking geometry quality
GPU / AI Environment Setup

For Method 2 AI refinement experiments, a CUDA-capable GPU is recommended.

9. Check GPU
```bash
nvidia-smi
WSL / Ubuntu
nvidia-smi
```
Optional Separate Environments
Some research models and AI completion pipelines require separate virtual environments because their dependencies may conflict with the main backend.
Examples:
Nerfstudio environment
PoinTr environment
other point cloud completion model environments
It is recommended to keep such environments separate from the main ORCA backend environment.
Example:
```bash
python -m venv venv_method2
venv_method2\Scripts\activate
```
or on Linux:
```bash
python3 -m venv venv_method2
source venv_method2/bin/activate
Running the Backend
```
After installation, start the development server:
```bash
uvicorn app.main:app --reload
```
If your main entry file is different, update the command accordingly.
Verification Checklist
Before running reconstruction pipelines, make sure the following work correctly:
```bash
python --version
pip --version
colmap -h
ffmpeg -version
```
If using GPU-based AI refinement:
```bash
nvidia-smi
```



