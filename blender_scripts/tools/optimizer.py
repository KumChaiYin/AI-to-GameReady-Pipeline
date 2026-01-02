import bpy
from tools.common import suppress_output

def optimize_static(obj, ratio=0.1):
    """Pipeline for Static Props (Decimate)."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    print(f">>> Optimizing Static Mesh: {obj.name}")
    
    # 1. Pre-Cleanup
    with suppress_output():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.001)
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    
    # 2. Decimate
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
    mod.ratio = ratio
    with suppress_output():
        bpy.ops.object.modifier_apply(modifier="Decimate")
    
    # 3. Post-Cleanup (Fix Invalid Mesh)
    with suppress_output():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.001)
        bpy.ops.mesh.delete_loose()
        bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.mesh.normals_make_consistent(inside=False)
    
    # 4. Validation
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.validate(verbose=False, clean_customdata=True)

def optimize_animatable(obj, voxel_size=0.005, target_faces=10000):
    """Pipeline for Characters (Voxel + Quadriflow) with robust fallback."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    print(f">>> Optimizing Animatable Mesh: {obj.name}")
    
    # 1. Voxel Remesh (Fix geometry volume)
    remesh = obj.modifiers.new(name="Remesh", type='REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = voxel_size
    bpy.ops.object.modifier_apply(modifier="Remesh")
    
    # 2. Quadriflow Prep (Cleanup)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action='SELECT')

    with suppress_output():
        bpy.ops.mesh.remove_doubles(threshold=0.001)
        bpy.ops.mesh.fill_holes(sides=0) 
        bpy.ops.mesh.delete_loose()

    # Normalize normals to help Quadriflow
    bpy.ops.mesh.normals_make_consistent(inside=False)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 3. Quadriflow with Return Code Check
    print(">>> Running Quadriflow...")
    quadriflow_success = False
    
    try:
        # We capture the return set. If it doesn't contain 'FINISHED', it failed.
        with suppress_output():
            ret = bpy.ops.object.quadriflow_remesh(
                use_preserve_sharp=True,
                use_preserve_boundary=True, 
                use_mesh_symmetry=False, 
                mode='FACES', 
                target_faces=target_faces
            )
        if 'FINISHED' in ret:
            quadriflow_success = True
    except Exception as e:
        print(f"Quadriflow threw exception: {e}")

    # 4. Fallback if Quadriflow failed (caught exception OR returned CANCELLED)
    if not quadriflow_success:
        print(f"Warning: Quadriflow failed or was cancelled. Using Decimate fallback.")
        
        # Ensure we are in Object mode before adding modifiers
        if bpy.context.object.mode != 'OBJECT':
             bpy.ops.object.mode_set(mode='OBJECT')

        mod = obj.modifiers.new(name="Decimate_Fallback", type='DECIMATE')
        mod.ratio = 0.1
        mod.use_collapse_triangulate = True 
        bpy.ops.object.modifier_apply(modifier="Decimate_Fallback")
    else:
        print(">>> Quadriflow Success.")

    # 5. Shade Smooth
    bpy.ops.object.shade_smooth()

def uv_unwrap(obj):
    """Smart UV Project."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # Safety Check: If mesh has no faces, UV Project will crash or fail
    if len(obj.data.polygons) > 0:
        bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.03)
    else:
        print(f"Error: Object {obj.name} has no faces to unwrap!")

    bpy.ops.object.mode_set(mode='OBJECT')