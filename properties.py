import bpy
from bpy.props import EnumProperty, PointerProperty

def get_uv_maps(self, context):
    obj = context.active_object
    if obj and obj.type == 'MESH':
        return [(uv.name, uv.name, "") for uv in obj.data.uv_layers]
    return []

class UVTransferProperties(bpy.types.PropertyGroup):
    layout_uv: EnumProperty(
        name="布局UV层",
        description="选择用于创建面片的UV层",
        items=get_uv_maps
    )

classes = (
    UVTransferProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.uv_transfer_props = PointerProperty(type=UVTransferProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.uv_transfer_props 