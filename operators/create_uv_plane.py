import bpy
import bmesh
from mathutils import Vector
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty

class UV_OT_create_uv_plane(Operator):
    bl_idname = "uv.create_uv_plane"
    bl_label = "从UV创建网格"
    bl_description = "基于UV边界创建网格模型"
    bl_options = {'REGISTER', 'UNDO'}
    
    process_collection: BoolProperty(
        name="处理集合",
        description="处理选中集合中的所有网格物体",
        default=False
    )
    
    @classmethod
    def poll(cls, context):
        if not bpy.context.active_object:
            return False
        if bpy.context.active_object.type != 'MESH':
            return False
        if not bpy.context.object.data.uv_layers:
            return False
        return True
    
    def create_mesh_from_uv(self, context, source_obj, uv_layer_name):
        # 保存当前模式
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # 创建新对象
        mesh_obj = source_obj.copy()
        mesh_obj.data = source_obj.data.copy()
        context.collection.objects.link(mesh_obj)
        mesh_obj.name = source_obj.name + "_UV_Mesh"
        
        # 选择新对象
        bpy.ops.object.select_all(action='DESELECT')
        mesh_obj.select_set(True)
        context.view_layer.objects.active = mesh_obj
        
        # 处理形态键
        if mesh_obj.data.shape_keys:
            if len(mesh_obj.data.shape_keys.key_blocks) > 1:
                for i in range(len(mesh_obj.data.shape_keys.key_blocks)):
                    context.object.active_shape_key_index = 0
                    bpy.ops.object.shape_key_remove(all=False)
        
        # 保存原始变换
        original_location = source_obj.location.copy()
        original_rotation = source_obj.rotation_euler.copy()
        original_scale = source_obj.scale.copy()
        
        # 进入编辑模式并获取bmesh
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(mesh_obj.data)
        
        # 确保使用第二套UV
        if len(bm.loops.layers.uv) >= 2:
            uv_layer = bm.loops.layers.uv[1]  # 使用第二套UV
        else:
            self.report({'ERROR'}, "物体需要至少两个UV层")
            return {'CANCELLED'}
        
        # 获取源对象的世界矩阵
        source_matrix = source_obj.matrix_world
        source_matrix_inv = source_matrix.inverted()
        
        # 保存原始顶点位置（考虑世界空间变换）
        original_coords = {}
        for vert in bm.verts:
            # 将顶点转换到世界空间
            world_co = source_matrix @ vert.co
            original_coords[vert.index] = world_co
        
        # 重塑网格以匹配UV
        scale_factor = 5000.0
        for face in bm.faces:
            for loop in face.loops:
                uv = loop[uv_layer].uv
                loop.vert.co = Vector((uv.x * scale_factor, uv.y * scale_factor, 0))
        
        # 更新网格
        bmesh.update_edit_mesh(mesh_obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # 添加形态键
        basis_key = mesh_obj.shape_key_add(name="model", from_mix=False)
        uv_key = mesh_obj.shape_key_add(name="uv", from_mix=False)
        
        # 设置基础形态键（原始形状）
        for vert_idx, world_co in original_coords.items():
            # 将世界空间坐标转换回局部空间
            local_co = source_matrix_inv @ world_co
            basis_key.data[vert_idx].co = local_co
        
        # 设置UV形态键（UV平面形状）
        for vert in mesh_obj.data.vertices:
            uv_key.data[vert.index].co = vert.co.copy()
        
        # 设置形态键和变换
        mesh_obj.active_shape_key_index = 0
        mesh_obj.active_shape_key.value = 1.0
        
        # 将物体移动到原点，但保持原始缩放和旋转
        mesh_obj.location = (0, 0, 0)  # 修改这里，直接设置为原点
        mesh_obj.rotation_euler = original_rotation
        mesh_obj.scale = original_scale
        
        # 切换到UV形态
        mesh_obj.active_shape_key_index = 1
        mesh_obj.active_shape_key.value = 1.0
        
        return {'FINISHED'}
    
    def execute(self, context):
        if self.process_collection:
            active_obj = context.active_object
            if not active_obj or active_obj.type != 'MESH':
                self.report({'ERROR'}, "请选择一个网格物体")
                return {'CANCELLED'}
            
            # 获取活动物体所在的集合
            source_collection = None
            for collection in bpy.data.collections:
                if active_obj.name in collection.objects:
                    source_collection = collection
                    break
                    
            if not source_collection:
                self.report({'ERROR'}, "活动体不在任何集合中")
                return {'CANCELLED'}
            
            # 创建或获取目标集合
            target_collection_name = source_collection.name + "_UV_Meshes"
            target_collection = bpy.data.collections.get(target_collection_name)
            if not target_collection:
                target_collection = bpy.data.collections.new(target_collection_name)
                bpy.context.scene.collection.children.link(target_collection)
            
            # 获取源集合中的所有网格物体
            mesh_objects = [obj for obj in source_collection.objects 
                           if obj.type == 'MESH' 
                           and len(obj.data.uv_layers) >= 2
                           and not obj.name.endswith("_UV_Mesh")]
            
            if not mesh_objects:
                self.report({'ERROR'}, "集合中没有合适的网格物体")
                return {'CANCELLED'}
            
            # 检查并删除所有物体的形态键
            for obj in mesh_objects:
                if obj.data.shape_keys:
                    # 选择并激活当前物体
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
                    
                    # 确保在物体模式
                    if context.mode != 'OBJECT':
                        bpy.ops.object.mode_set(mode='OBJECT')
                    
                    # 删除所有形态键
                    while obj.data.shape_keys:
                        obj.shape_key_clear()
            
            # 保存当前状态
            original_active = context.active_object
            original_mode = context.mode
            
            # 确保在物体模式
            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # 保存第一个生成的UV片作为数据源
            first_uv_mesh = None
            processed = 0
            
            try:
                for i, obj in enumerate(mesh_objects):
                    # 保存原始名称
                    original_name = obj.name
                    
                    # 创建UV面片
                    result = self.create_mesh_from_uv(context, obj, None)
                    if result == {'FINISHED'}:
                        # 获取新创建的UV片
                        new_obj = context.active_object
                        
                        # 从当前集合中移除并添加到目标集合
                        for c in new_obj.users_collection:
                            c.objects.unlink(new_obj)
                        target_collection.objects.link(new_obj)
                        
                        # 如果是第一个物体，保存为数据源并删除第二套UV
                        if i == 0:
                            first_uv_mesh = new_obj
                            # 只删除第一个物体的第二套UV
                            if len(new_obj.data.uv_layers) >= 2:
                                new_obj.data.uv_layers.remove(new_obj.data.uv_layers[1])
                        else:
                            # 为其他UV片添加Data Transfer修改器
                            dt_mod = new_obj.modifiers.new(name="DataTransfer", type='DATA_TRANSFER')
                            dt_mod.object = first_uv_mesh
                            dt_mod.use_loop_data = True
                            dt_mod.data_types_loops = {'UV'}
                            dt_mod.loop_mapping = 'NEAREST_POLYNOR'
                            
                            # 设置UV层映射
                            if len(first_uv_mesh.data.uv_layers) >= 2:
                                src_uv_name = first_uv_mesh.data.uv_layers[1].name
                            else:
                                src_uv_name = first_uv_mesh.data.uv_layers[0].name
                            
                            if len(new_obj.data.uv_layers) >= 2:
                                dst_uv_name = new_obj.data.uv_layers[1].name
                            else:
                                dst_uv_name = new_obj.data.uv_layers[0].name
                            
                            dt_mod.layers_uv_select_src = src_uv_name
                            dt_mod.layers_uv_select_dst = dst_uv_name
                            
                            # 应用修改器
                            context.view_layer.objects.active = new_obj
                            bpy.ops.object.modifier_apply(modifier=dt_mod.name)
                        
                        # 重命名原始物体和新物体
                        obj.name = original_name + "_ori"
                        new_obj.name = original_name
                        
                        # 删除原始物体的第三套UV
                        if len(obj.data.uv_layers) >= 3:
                            obj.data.uv_layers.remove(obj.data.uv_layers[2])
                        
                        processed += 1
            
                # 处理完所有物体后，将所有UV片恢复到原始形状并应用形态键
                for obj in target_collection.objects:
                    if obj.data.shape_keys and "model" in obj.data.shape_keys.key_blocks:
                        # 切换到基础形态键并设置值
                        obj.active_shape_key_index = 0
                        obj.data.shape_keys.key_blocks["uv"].value = 0.0
                        
                        # 选择并激活当前物体
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(True)
                        context.view_layer.objects.active = obj
                        
                        # 应用所有形态键
                        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
            
                self.report({'INFO'}, f"已处理 {processed} 个物体，结果保存在集合 '{target_collection_name}' 中")
                return {'FINISHED'}
            
            except Exception as e:
                self.report({'ERROR'}, f"处理过程中出错: {str(e)}")
                return {'CANCELLED'}
            
            finally:
                # 恢复原始状态
                bpy.ops.object.select_all(action='DESELECT')
                if original_active:
                    original_active.select_set(True)
                    context.view_layer.objects.active = original_active
                
                if original_mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode=original_mode)
            
        else:
            obj = context.active_object
            if not obj or obj.type != 'MESH':
                self.report({'ERROR'}, "请选择一个网格物体")
                return {'CANCELLED'}
            
            if len(obj.data.uv_layers) < 2:
                self.report({'ERROR'}, "物体需要至少两个UV层")
                return {'CANCELLED'}
            
            # 检查并删除形态键
            if obj.data.shape_keys:
                # 确保在物体模式
                if context.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                
                # 删除所有形态键
                obj.shape_key_clear()
            
            # 保存原始名称
            original_name = obj.name
            
            result = self.create_mesh_from_uv(context, obj, None)
            
            if result == {'FINISHED'}:
                # 为单个物体处理也创建集合
                target_collection_name = "UV_Meshes"
                target_collection = bpy.data.collections.get(target_collection_name)
                if not target_collection:
                    target_collection = bpy.data.collections.new(target_collection_name)
                    bpy.context.scene.collection.children.link(target_collection)
                
                # 移动新创建的物体到目标集合
                new_obj = context.active_object
                for c in new_obj.users_collection:
                    c.objects.unlink(new_obj)
                target_collection.objects.link(new_obj)
            
                # 恢复到原始形状并应用形态键
                if new_obj.data.shape_keys and "model" in new_obj.data.shape_keys.key_blocks:
                    new_obj.active_shape_key_index = 0
                    new_obj.data.shape_keys.key_blocks["uv"].value = 0.0
                    
                    # 确保物体被选中和激活
                    bpy.ops.object.select_all(action='DESELECT')
                    new_obj.select_set(True)
                    context.view_layer.objects.active = new_obj
                    
                    # 应用所有形态键
                    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
                
                # 重命名原始物体和新物体
                obj.name = original_name + "_ori"
                new_obj.name = original_name
                
                # 删除原始物体的第三套UV
                if len(obj.data.uv_layers) >= 3:
                    obj.data.uv_layers.remove(obj.data.uv_layers[2])
                
                # 删除新物体的第二套UV
                if len(new_obj.data.uv_layers) >= 2:
                    new_obj.data.uv_layers.remove(new_obj.data.uv_layers[1])
            
            return result

classes = (
    UV_OT_create_uv_plane,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)