import subprocess
import os
import sys

# ----- Configuration -----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRIPO_DIR = os.path.join(BASE_DIR, "TripoSR")

BLENDER_SCRIPT = os.path.join(BASE_DIR, "blender_process.py")

INPUT_IMG = os.path.join(BASE_DIR, "input_images", "character.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

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
    generated_obj = os.path.join(OUTPUT_DIR, "mesh.obj")



if __name__ == "__main__":
    run_pipeline()
    




