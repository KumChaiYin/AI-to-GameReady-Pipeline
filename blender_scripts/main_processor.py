import bpy
import sys
import os
import argparse
import logging

# 1. LOAD TOOLS
dir_path = os.path.dirname(os.path.realpath(__file__))
if dir_path not in sys.path:
    sys.path.append(dir_path)

from tools import common, optimizer, baker

# 2. ARGUMENT PARSING
def get_args():
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=["static", "animatable"], required=True)

    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging for debugging")

    return parser.parse_args(argv)

# 3. MAIN PIPELINE
def main():
    args = get_args()
    common.set_verbose(args.verbose)
    
    # A. Setup
    common.clean_scene()
    import_obj = common.import_model(args.input)
    
    if not import_obj:
        print("Error: Import failed.")
        return

    # B. Branching Logic
    if args.mode == "static":
        # --- STATIC FLOW ---
        target_obj = import_obj

        # 1. Create Backup for Data Transfer
        source_obj = common.duplicate_object(target_obj, name="Source_HighPoly")
        source_obj.hide_viewport = True
        
        # 2. Geometry Optimization
        optimizer.optimize_static(target_obj, ratio=0.1)
        
        # 3. Restore Colors
        baker.transfer_vertex_colors(target=target_obj, source=source_obj)
        baker.setup_static_material(target_obj)

    elif args.mode == "animatable":
        # --- ANIMATABLE FLOW ---
        # 1. Setup Source (Rename original imported obj)
        source_obj = import_obj
        source_obj.name = "Source_HighPoly"
        
        # 2. Setup Source Material (if texture provided)
        baker.setup_cycles_baking()

        input_dir = os.path.dirname(args.input)
        source_texture_path = os.path.join(input_dir, "texture.png")
        baker.setup_source_texture(source_obj, source_texture_path)

        # 3. Create Target (Duplicate)
        target_obj = common.duplicate_object(source_obj, name="Target_LowPoly")
        
        # 4. Geometry Optimization
        optimizer.optimize_animatable(target_obj)
        optimizer.uv_unwrap(target_obj)
        
        # 5. Baking
        baker.bake_textures(target=target_obj, source=source_obj)
    
    # C. Clean Source and Export
    bpy.data.objects.remove(source_obj, do_unlink=True)
    common.export_model(target_obj, args.output)

if __name__ == "__main__":
    main()