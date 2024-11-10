import bpy
from bpy.types import Panel

class UV_PT_transfer_panel(Panel):
    bl_label = "UV Transfer Tool"
    bl_idname = "UV_PT_transfer_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UV Transfer'
    
    def draw(self, context):
        layout = self.layout
        
        # 创建网格按钮（单个物体）
        op = layout.operator("uv.create_uv_plane", text="从UV创建网格")
        op.process_collection = False
        
        # 创建网格按钮（同集合物体）
        op = layout.operator("uv.create_uv_plane", text="处理同集合中的所有物体")
        op.process_collection = True
        
        # 如果选中的物体有形态键，显示形态键值滑块
        obj = context.active_object
        if obj and obj.type == 'MESH' and obj.data.shape_keys:
            key_block = obj.data.shape_keys.key_blocks.get('uv')
            if key_block:
                layout.prop(key_block, "value", text="UV形状")
        
        # 使用说明
        box = layout.box()
        box.label(text="使用说明：")
        box.label(text="1. 选择要转换的模型")
        box.label(text="2A. 点击'从UV创建网格'处理单个物体")
        box.label(text="2B. 点击'处理同集合中的所有物体'批量处理")
        box.label(text="3. 使用滑块切换形状")

classes = (
    UV_PT_transfer_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 