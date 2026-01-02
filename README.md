# AI-to-GameReady Asset Pipeline

An automated pipeline that generates 3D models from 2D images using **TripoSR** and optimizes them using **Blender**.

The pipeline handles generation, geometry optimization (Decimation/Remeshing), UV unwrapping, and Texture Baking (Normal/Diffuse) automatically.

## ✨ Features

* **Two Optimization Modes:**
    * **Static:** Fast optimization for props (Decimation + Vertex Colors).
    * **Animatable:** High-quality quad topology (Voxel + Quadriflow) + Texture Baking (Diffuse & Normal Maps).
* **Automated Blender Processing:** No manual work required.
* **Robust Logging:** Clean console output by default, with an optional `--verbose` flag for debugging.

## ⚠️ System Requirements & Compatibility

This project has been developed and tested under the following environment. Usage on other systems is **experimental**.

* **OS:** Windows 11
* **Python:** 3.10
* **Blender:** 4.x / 5.0+ (tested on 5.0)
* **GPU:** NVIDIA GPU with **CUDA 11.8** installed.
    * *Note:* Newer CUDA versions (12.x) may fail to compile `torchmcubes` due to missing NVTX headers on Windows.

## Getting Started

### 1. Clone the Repo
```bash
git clone https://github.com/KumChaiYin/AI-to-GameReady-Pipeline.git
cd AI-to-GameReady-Pipeline

```

### 2. Install PyTorch (CUDA 11.8 version)

You must install the version of PyTorch that matches your CUDA Toolkit **before** installing other requirements.

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

```

### 3. Install Pipeline Dependencies

This step will compile `torchmcubes`. It may take a few minutes.

```bash
pip install -r requirements.txt

```

### 4. Configuration

Create a `.env` file in the root directory and set your Blender path:

```ini
BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe

```


## 🏃 Usage

Run the pipeline using `run.py`.

### Basic Usage (Static Prop)

Best for background items, rocks, or hard-surface objects.

```bash
# Example
python run.py images/character.png --mode static

```

### Character Usage (Animatable)

Best for characters. Performs Voxel Remeshing, Quadriflow, and Texture Baking.

```bash
# Example
python run.py images/character.png --mode animatable

```

### Debugging

If Blender fails, use verbose mode to see the internal logs:

```bash
# Example
python run.py images/character.png --mode animatable --verbose

```


## 🛠 Troubleshooting

### 1. "Failed to build installable wheels for torchmcubes"

This is a common error on Windows when the CUDA environment is not perfectly matched.

**Solution:**

1. Ensure you have **CUDA Toolkit 11.8** installed.
2. If you are using **CUDA 12.x** and cannot downgrade, you may need to manually install the legacy NVTX headers or follow the fix detailed in this thread:
* [TripoSR Issue #74: Installation Fix for CUDA 12.x](https://github.com/VAST-AI-Research/TripoSR/issues/74)

### 2. "Blender command not found"

Check your `.env` file and ensure `BLENDER_PATH` points to the actual `blender.exe` file, not just the folder.