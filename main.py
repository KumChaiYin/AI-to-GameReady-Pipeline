import subprocess
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ----- Configuration -----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRIPO_DIR = os.path.join(BASE_DIR, "TripoSR")

BLENDER_SCRIPT = os.path.join(BASE_DIR, "blender_process.py")

INPUT_IMG = os.path.join(BASE_DIR, "input_images", "character.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

BLENDER_EXE = os.getenv("BLENDER_PATH")

if not BLENDER_EXE:
    raise ValueError("Please set BLENDER_PATH in your .env file")

def run_pipeline():
    print(">>> Stage 1: Running AI Generation (TripoSR)...")
    
    abs_input_img = os.path.abspath(INPUT_IMG)
    abs_output_dir = os.path.abspath(OUTPUT_DIR)

    tripo_args = [
        "python", "run.py",
        abs_input_img,
        "--output-dir", abs_output_dir
    ]
    
    # Executes the command "inside" the TripoSR folder.
    subprocess.run(tripo_args, cwd=TRIPO_DIR, check=True)
    
    # Name of the generated file (TripoSR outputs 'mesh.obj')
    generated_obj = os.path.join(OUTPUT_DIR, "0", "mesh.obj")

    if not os.path.exists(generated_obj):
        raise ValueError("Check the path storing the generated mesn.obj")

    print(f">>> Stage 2: Processing {generated_obj} in Blender...")

    # Construct the Blender command:
    # -b : Run in background mode (no UI)
    # -P : Run the specified Python script
    # -- : Pass arguments after this flag to the Python script
    blender_args = [
        BLENDER_EXE,
        "--background",
        "--python", BLENDER_SCRIPT,
        "--",
        generated_obj, # Argument 1 for blender script
        os.path.join(OUTPUT_DIR, "final_asset.glb") # Argument 2 for blender script
    ]
    
    subprocess.run(blender_args, check=True)
    
    print(">>> Pipeline Finished!")


if __name__ == "__main__":
    run_pipeline()
    




