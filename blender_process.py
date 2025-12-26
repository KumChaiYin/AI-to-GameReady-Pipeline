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
        # attr_node.location = (-300, 0) # Move node to left for clarity

        # Link the Attribute Color output to the Base Color input of the Shader
        if bsdf:
            mat.node_tree.links.new(attr_node.outputs["Color"], bsdf.inputs["Base Color"])

        # Assign the material to the object
        obj.data.materials.append(mat)

    # 4. Export
    print(f"Exporting to: {OUTPUT_FILE}")
    bpy.ops.export_scene.gltf(filepath=OUTPUT_FILE)

if __name__ == "__main__":
    pipeline_logic()