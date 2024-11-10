bl_info = {
    "name": "UV Transfer Tool",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (4, 2, 3),
    "location": "View3D > Sidebar > UV Transfer",
    "description": "Convert mesh to UV plane based on selected UV map",
    "category": "UV",
}

import bpy
from . import operators
from . import ui
from . import properties

modules = (
    properties,
    operators,
    ui,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register() 