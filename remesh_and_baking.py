import bpy
import sys
import os
import math

argv = sys.argv
argv = argv[argv.index("--") + 1:]
INPUT_OBJ = argv[0]
OUTPUT_GLB = argv[1]

INPUT_DIR = os.path.dirname(INPUT_OBJ)
SOURCE_TEXTURE = os.path.join(INPUT_DIR, "texture.png") 

def pipeline_logic():
    # 1. Setup
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Switch to CYCLES (Required for Baking)
    bpy.context.scene.render.engine = 'CYCLES'
    try:
        bpy.context.scene.cycles.device = 'GPU'
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA' 
    except:
        pass
    bpy.context.scene.cycles.samples = 16

    # 2. Import model
    if INPUT_OBJ.endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=INPUT_OBJ)
    
    if not bpy.context.selected_objects:
        print("No object imported!")
        return
    
    source_obj = bpy.context.selected_objects[0]
    source_obj.name = "Source_HighPoly"

    # Ensure source has texture
    if os.path.exists(SOURCE_TEXTURE):
        if not source_obj.data.materials:
            mat = bpy.data.materials.new(name="SourceMat")
            source_obj.data.materials.append(mat)
        
        mat = source_obj.data.materials[0]
        bsdf = mat.node_tree.nodes.get("Principled BSDF")

        has_image = False
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                has_image = True
                break
        
        if not has_image:
            print(f"Linking texture: {SOURCE_TEXTURE}")
            tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex_node.image = bpy.data.images.load(SOURCE_TEXTURE)
            if bsdf:
                mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        print(f"Warning: Source texture not found at {SOURCE_TEXTURE}")

    # 3. Create Target (Optimization)
    bpy.ops.object.select_all(action='DESELECT')
    source_obj.select_set(True)
    bpy.context.view_layer.objects.active = source_obj
    bpy.ops.object.duplicate()
    target_obj = bpy.context.selected_objects[0]
    target_obj.name = "Target_LowPoly"

    bpy.ops.object.mode_set(mode='OBJECT')

    # 3.1. Voxel Remesh (Struxture)
    remesh = target_obj.modifiers.new(name="Remesh", type='REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = 0.005 
    bpy.ops.object.modifier_apply(modifier="Remesh")

    # 3.2. Decimate (Planar Mode)
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = target_obj.modifiers.new(name="Decimate", type='DECIMATE')
    mod.ratio = 0.1
    bpy.ops.object.modifier_apply(modifier="Decimate")
    
    # decimate = target_obj.modifiers.new(name="Decimate", type='DECIMATE')
    # decimate.decimate_type = 'DISSOLVE' 
    # decimate.angle_limit = math.radians(20) # preserve sharp corner (doesn't look good on the character)
    # bpy.ops.object.modifier_apply(modifier="Decimate")

    # 4. UV Unwrap
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.03)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 5. Baking
    target_mat = bpy.data.materials.new(name="Final_Game_Mat")
    target_obj.data.materials.clear()
    target_obj.data.materials.append(target_mat)
    
    target_bsdf = target_mat.node_tree.nodes.get("Principled BSDF")
    if target_bsdf:
        target_bsdf.inputs["Roughness"].default_value = 0.7
    
    bake_image = bpy.data.images.new("Final_Texture", width=1024, height=1024)
    
    tex_image_node = target_mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_image_node.image = bake_image
    target_mat.node_tree.nodes.active = tex_image_node

    bpy.ops.object.select_all(action='DESELECT')
    source_obj.select_set(True)
    target_obj.select_set(True)
    bpy.context.view_layer.objects.active = target_obj

    print(">>> Starting Bake (High to Low)...")
    # Using 'DIFFUSE' with only 'COLOR' ensures we don't bake shadows/lighting
    bpy.ops.object.bake(
        type='DIFFUSE',
        pass_filter={'COLOR'},
        use_selected_to_active=True,
        cage_extrusion=0.03, 
        target='IMAGE_TEXTURES'
    )

    if target_bsdf:
        target_mat.node_tree.links.new(tex_image_node.outputs["Color"], target_bsdf.inputs["Base Color"])

    # 6. Export
    bpy.ops.object.select_all(action='DESELECT')
    source_obj.select_set(True)
    bpy.ops.object.delete()
    
    target_obj.select_set(True)
    
    print(f"Exporting Final Asset to: {OUTPUT_GLB}")
    bpy.ops.export_scene.gltf(filepath=OUTPUT_GLB, export_format='GLB', export_apply=True)

if __name__ == "__main__":
    pipeline_logic()