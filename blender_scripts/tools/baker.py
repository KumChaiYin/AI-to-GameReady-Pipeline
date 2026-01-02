import bpy
import os
from tools.common import suppress_output

# --- STATIC PIPELINE TOOLS ---
def transfer_vertex_colors(target, source):
    """Restores colors from Source to Target via Data Transfer."""
    print(">>> Restoring Vertex Colors...")
    
    if not target.data.color_attributes:
        target.data.color_attributes.new(name="Target_Color", type='BYTE_COLOR', domain='CORNER')
        
    dt_mod = target.modifiers.new(name="ColorTransfer", type='DATA_TRANSFER')
    dt_mod.object = source
    dt_mod.use_loop_data = True
    # Note: 'COLOR_CORNER' is for Blender 3.2+
    dt_mod.data_types_loops = {'COLOR_CORNER'} 
    dt_mod.loop_mapping = 'NEAREST_POLYNOR'
    
    bpy.ops.object.modifier_apply(modifier="ColorTransfer")

def setup_static_material(obj):
    """Sets up a material that displays Vertex Colors."""
    if not obj.data.color_attributes: return

    obj.data.materials.clear()
    
    mat = bpy.data.materials.new(name="Static_VCol_Mat")
    bsdf = mat.node_tree.nodes.get("Principled BSDF")

    attr_node = mat.node_tree.nodes.new(type="ShaderNodeAttribute")
    
    # Important: Use exact layer name
    attr_node.attribute_name = obj.data.color_attributes.active.name
    
    if bsdf:
        mat.node_tree.links.new(attr_node.outputs["Color"], bsdf.inputs["Base Color"])
    
    obj.data.materials.append(mat)

# --- ANIMATABLE PIPELINE TOOLS ---
def setup_cycles_baking():
    """Configures Cycles for baking."""
    bpy.context.scene.render.engine = 'CYCLES'
    try:
        bpy.context.scene.cycles.device = 'GPU'
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'
    except: 
        pass
    bpy.context.scene.cycles.samples = 16

def setup_source_texture(source_obj, texture_path):
    """
    Checks if a texture exists and links it to the source object's material.
    """
    # 1. Safety Check: File exists?
    if not texture_path or not os.path.exists(texture_path):
        print(f"Warning: Source texture not found at: {texture_path}")
        return

    print(f">>> Linking Source Texture: {os.path.basename(texture_path)}")

    # 2. Material Setup (Get or Create)
    if not source_obj.data.materials:
        mat = bpy.data.materials.new(name="Source_Mat")
        source_obj.data.materials.append(mat)
    else:
        mat = source_obj.data.materials[0]
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")

    # 3. Check if image is already loaded (Avoid duplication)
    for node in nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            if node.image.filepath == texture_path:
                print("Texture already linked. Skipping.")
                return

    # 4. Create and Link Node
    tex_node = nodes.new('ShaderNodeTexImage')
    try:
        tex_node.image = bpy.data.images.load(texture_path)
    except RuntimeError:
        print(f"Error: Blender could not load image: {texture_path}")
        return

    if bsdf:
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

def bake_textures(target, source):
    """Bakes Diffuse and Normal maps."""
    
    # 1. Setup Material for Baking
    target_mat = bpy.data.materials.new(name="Final_Game_Mat")
    target.data.materials.clear()
    target.data.materials.append(target_mat)
    
    # Nodes
    target_bsdf = target_mat.node_tree.nodes.get("Principled BSDF")
    target_bsdf.inputs["Roughness"].default_value = 0.7
    
    # 2. Create Image Nodes
    bake_image = bpy.data.images.new("Final_Texture", width=1024, height=1024)
    tex_image_node = target_mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_image_node.image = bake_image
    
    bake_normal = bpy.data.images.new("Final_Normal", width=1024, height=1024)
    bake_normal.colorspace_settings.name = 'Non-Color' 
    tex_normal_node = target_mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_normal_node.image = bake_normal
    
    # 3. Bake Process
    bpy.ops.object.select_all(action='DESELECT')
    source.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    
    # --- Bake Color ---
    print(">>> Baking Color...")
    target_mat.node_tree.nodes.active = tex_image_node
    with suppress_output():
        bpy.ops.object.bake(
            type='DIFFUSE', 
            pass_filter={'COLOR'}, 
            use_selected_to_active=True, 
            cage_extrusion=0.03,
            target='IMAGE_TEXTURES'
        )
    
    # --- Bake Normal ---
    print(">>> Baking Normal...")
    target_mat.node_tree.nodes.active = tex_normal_node
    with suppress_output():
        bpy.ops.object.bake(
            type='NORMAL', 
            use_selected_to_active=True, 
            cage_extrusion=0.03,
            target='IMAGE_TEXTURES'
        )
    
    # 4. Link Nodes for Export
    target_mat.node_tree.links.new(tex_image_node.outputs["Color"], target_bsdf.inputs["Base Color"])
    
    normal_map_node = target_mat.node_tree.nodes.new('ShaderNodeNormalMap')
    target_mat.node_tree.links.new(tex_normal_node.outputs["Color"], normal_map_node.inputs["Color"])
    target_mat.node_tree.links.new(normal_map_node.outputs["Normal"], target_bsdf.inputs["Normal"])