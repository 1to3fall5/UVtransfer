from . import create_uv_plane

modules = (
    create_uv_plane,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister() 