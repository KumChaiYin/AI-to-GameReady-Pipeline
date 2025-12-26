import bpy
import sys
import os

argv = sys.argv
argv = argv[argv.index("--") + 1:] 
INPUT_FILE = argv[0]
OUTPUT_FILE = argv[1]

def pipeline_logic():
    print(f"from blender_process: {INPUT_FILE}")
    print(f"from blender_process: {OUTPUT_FILE}")

if __name__ == "__main__":
    pipeline_logic()