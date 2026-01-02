import bpy
import os
import sys
from contextlib import contextmanager

# Global variable to store verbose state (Default is False/Silent)
_VERBOSE_MODE = False

def set_verbose(enabled: bool):
    """Sets the global verbose mode for tools."""
    global _VERBOSE_MODE
    _VERBOSE_MODE = enabled
    print(f">>> Verbose Mode Set to: {enabled}")

@contextmanager
def suppress_output():
    """
    Suppresses stdout/stderr unless Verbose Mode is ON.
    """
    # IF user wants verbose logs, do nothing (allow print)
    if _VERBOSE_MODE:
        yield
        return

    # ELSE, redirect to black hole
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

def clean_scene():
    """Deletes everything in the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def import_model(file_path):
    """Imports OBJ or PLY."""
    if file_path.endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=file_path)
    elif file_path.endswith(".ply"):
        bpy.ops.wm.ply_import(filepath=file_path)
    
    if bpy.context.selected_objects:
        return bpy.context.selected_objects[0]
    return None

def export_model(obj, file_path, export_colors=True):
    """Standard glTF export."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    print(f">>> Exporting to: {file_path}")

    try:
        with suppress_output():
            bpy.ops.export_scene.gltf(
                filepath=file_path, 
                export_format='GLB',
                export_apply=True, 
                export_attributes=export_colors, 
                use_selection=True
            )
    except Exception as e:
        raise e

def duplicate_object(obj, name=None):
    """
    Creates a deep copy of an object (independent mesh data).
    Does NOT rely on selection context (safer than bpy.ops).
    """
    # 1. Copy the Object wrapper
    new_obj = obj.copy()
    # 2. Deep copy the Mesh Data (so modifying one doesn't break the other)
    new_obj.data = obj.data.copy()
    # 3. Link to the scene
    bpy.context.collection.objects.link(new_obj)
    
    if name:
        new_obj.name = name
        
    return new_obj