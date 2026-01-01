import bpy
import sys
import os

argv = sys.argv
argv = argv[argv.index("--") + 1:] 
INPUT_FILE = argv[0]
OUTPUT_FILE = argv[1]

def pipeline_logic():
    # 1. Scene cleanup
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # 2. Import model
    if INPUT_FILE.endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=INPUT_FILE)
    elif INPUT_FILE.endswith(".ply"):
        bpy.ops.wm.ply_import(filepath=INPUT_FILE)
    
    if not bpy.context.selected_objects:
        print("No object imported!")
        return

    target_obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = target_obj # Set the active object

    # 3. Backup High Poly (source)
    source_obj = target_obj.copy()
    source_obj.data = target_obj.data.copy()
    source_obj.name = "Source_HighPoly"
    bpy.context.collection.objects.link(source_obj)

    if not source_obj.data.color_attributes:
        print("!!! WARNING: Source OBJ has no Vertex Colors! Output will be white.")
    else:
        print(f"Source Colors Detected: {[a.name for a in source_obj.data.color_attributes]}")
    
    source_obj.hide_viewport = True

    # Reset Target Selection
    bpy.ops.object.select_all(action='DESELECT')
    target_obj.select_set(True)
    bpy.context.view_layer.objects.active = target_obj
    
    # 4. Geometry Processing (Optimization & Cleanup)

    # 4.1. Pre-Decimate
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

    # 4.2. Decimate
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = target_obj.modifiers.new(name="Decimate", type='DECIMATE')
    mod.ratio = 0.1
    bpy.ops.object.modifier_apply(modifier="Decimate")

    # 4.3. Post-Cleanup
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.delete_loose()
    bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.mesh.normals_make_consistent(inside=False)

    # 4.4. Validation
    bpy.ops.object.mode_set(mode='OBJECT')
    target_obj.data.validate(verbose=False, clean_customdata=True)

    # 5. Data Transfer
    if not target_obj.data.color_attributes:
        target_obj.data.color_attributes.new(name="Target_Color", type='BYTE_COLOR', domain='CORNER')
    
    target_layer_name = target_obj.data.color_attributes.active.name

    dt_mod = target_obj.modifiers.new(name="ColorTransfer", type='DATA_TRANSFER')
    dt_mod.object = source_obj 
    dt_mod.use_loop_data = True 
    dt_mod.data_types_loops = {'COLOR_CORNER'}
    dt_mod.loop_mapping = 'NEAREST_POLYNOR'

    bpy.ops.object.modifier_apply(modifier="ColorTransfer")

    # 6. Material Setup
    target_obj.data.materials.clear()

    mat = bpy.data.materials.new(name="Final_VCol_Mat")
    bsdf = mat.node_tree.nodes.get("Principled BSDF")

    attr_node = mat.node_tree.nodes.new(type="ShaderNodeAttribute")
    attr_node.attribute_name = target_layer_name 

    if bsdf:
        mat.node_tree.links.new(attr_node.outputs["Color"], bsdf.inputs["Base Color"])

    target_obj.data.materials.append(mat)
 
    # 7. Final Export
    bpy.data.objects.remove(source_obj, do_unlink=True)
    
    print(f"Exporting to: {OUTPUT_FILE}")
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_FILE, 
        export_apply=True, 
        export_attributes=True
    )

if __name__ == "__main__":
    pipeline_logic()