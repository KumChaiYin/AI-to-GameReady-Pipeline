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

    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj # Set the active object

    # 3. Handle Vertex Colors
    if not obj.data.materials:
        # Create a new material
        mat = bpy.data.materials.new(name="VertexColorMat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")

        # Check if the mesh has color attributes
        color_layer_name = "Col"
        if hasattr(obj.data, "color_attributes") and obj.data.color_attributes:
            color_layer_name = obj.data.color_attributes.active.name 
        
        # Access vertex data
        attr_node = mat.node_tree.nodes.new(type="ShaderNodeAttribute")
        attr_node.attribute_name = color_layer_name

        # Link the Attribute Color output to the Base Color input of the Shader
        if bsdf:
            mat.node_tree.links.new(attr_node.outputs["Color"], bsdf.inputs["Base Color"])

        # Assign the material to the object
        obj.data.materials.append(mat)
    
    # 4. Geometry Processing (Optimization & Cleanup)

    # Switch to EDIT mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # 4.1. Merge Vertices
    bpy.ops.mesh.remove_doubles(threshold=0.001)

    # 4.2. Manifold Check (Auto-fill Holes)
    bpy.ops.mesh.fill_holes(sides=4)

    # # Voxel Remesh
    # bpy.ops.object.mode_set(mode='OBJECT')
    
    # # Add Remesh Modifier
    # remesh = obj.modifiers.new(name="VoxelRemesh", type='REMESH')
    # remesh.mode = 'VOXEL'
    # remesh.voxel_size = 0.01  # Smaller = More Detail, Higher Poly Count
    # remesh.adaptivity = 0.0
    
    # bpy.ops.object.modifier_apply(modifier="VoxelRemesh")

    # 4.3.1. Reduce poly count (Decimate)
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
    mod.ratio = 0.1
    bpy.ops.object.modifier_apply(modifier="Decimate")

    # 4.3.2. Cleanup after Decimate
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Merge vertices
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    # Delete loose geometry (Fixes floating points/edges that Decimate left behind)
    bpy.ops.mesh.delete_loose()
    # Dissolve degenerate (Fixes zero-area faces)
    bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
    # Clear custom split normals from imported OBJs
    try:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except AttributeError:
        pass # In case the mesh doesn't have custom normals, ignore error
    # Recalculate Normals (Ensure all faces point outward)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    
    # 4.4. Simple Tri-to-Quad (Fast Optimization)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.tris_convert_to_quads()
 
    # 5. Export
    print(f"Exporting to: {OUTPUT_FILE}")
    bpy.ops.export_scene.gltf(filepath=OUTPUT_FILE)

if __name__ == "__main__":
    pipeline_logic()