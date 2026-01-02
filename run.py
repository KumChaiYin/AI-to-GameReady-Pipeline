import subprocess
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

# ----- Configuration -----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRIPO_DIR = os.path.join(BASE_DIR, "TripoSR")

BLENDER_SCRIPT = os.path.join(BASE_DIR, "blender_scripts", "main_processor.py")

BLENDER_EXE = os.getenv("BLENDER_PATH")

if not BLENDER_EXE:
    raise ValueError("Please set BLENDER_PATH in your .env file")

def run_pipeline(input_image_path, output_dir, mode):
    abs_input_img = os.path.abspath(input_image_path)
    abs_output_dir = os.path.abspath(output_dir)

    if not os.path.exists(abs_output_dir):
        os.makedirs(abs_output_dir)

    print(">>> Stage 1: Running AI Generation (TripoSR)...")
    
    tripo_cmd = [
        "python", "run.py",
        abs_input_img,
        "--output-dir", abs_output_dir,
    ]

    if mode == "animatable":
        print("    -> Mode is Animatable: Enabling Texture Baking in TripoSR.")
        tripo_cmd.extend(["--bake-texture", "--texture-resolution", "1024"])
    else:
        print("    -> Mode is Static: Using Vertex Colors (No Baking). Fast generation.")

    try:
        subprocess.run(tripo_cmd, cwd=TRIPO_DIR, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error in Stage 1 (TripoSR): {e}")
        return
    
    # Name of the generated file (TripoSR outputs 'mesh.obj')
    generated_obj = os.path.join(abs_output_dir, "0", "mesh.obj")

    if not os.path.exists(generated_obj):
        print(f"Check the path storing the generated mesh.obj")
        return

    print(f">>> Stage 2: Processing {generated_obj} in Blender...")

    final_output_name = f"asset_{mode}.glb"
    final_output_path = os.path.join(abs_output_dir, final_output_name)
    
    blender_cmd = [
        BLENDER_EXE,
        "--background",                 
        "--python", BLENDER_SCRIPT,     
        "--",                           
        "--input", generated_obj,
        "--output", final_output_path,
        "--mode", mode                  
    ]
    
    try:
        subprocess.run(blender_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error in Stage 2 (Blender): {e}")
    
    print(">>> Pipeline Finished!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated AI-to-3D Pipeline")
    
    parser.add_argument("image", help="Path to the input image file")
    parser.add_argument("--output", default="./output", help="Directory to save output")
    parser.add_argument("--mode", choices=["static", "animatable"], default="static", 
                        help="Choose pipeline mode: 'static' (Props) or 'animatable' (Characters)")

    args = parser.parse_args()

    run_pipeline(args.image, args.output, args.mode)
