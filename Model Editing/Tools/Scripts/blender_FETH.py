bl_info = {
    "name": "FETH plugin",
    "description": "",
    "author": "Joschka",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "Properties > Bone and Properties > Object Data",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}


import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class MyProperties(PropertyGroup):

    my_int: IntProperty(
        name = "ib/vb number",
        description="ib/vb number",
        default = 0,
        min = 0,
        max = 100
        ) 

    my_path: StringProperty(
        name = "Bone bind file",
        description="Choose the bind file:",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
        )


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class OT_FETH_RENAME(Operator):
    bl_label = "Map bones"
    bl_idname = "feth.rename"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        obj = context.object
        map = {}
        rev_map={}
        with open(mytool.my_path) as f:
            u = "default"
            while(u != "sm_"+str(mytool.my_int)):
                u = f.readline().split()[0]		
            while(True):
                a,b = f.readline().split()
                a=int(a)
                b=int(b)
                if a < 0:
                    break
                map[a]=b
                rev_map[b]=a
        bone_groups = obj.pose.bone_groups
        if(not len(bone_groups)):
            bpy.ops.pose.group_add()
            pb_group = obj.pose.bone_groups['Group']
            pb_group.name = "FETH_bones"
        for pbone in obj.pose.bones:
            pbone.bone.select = False
            pbone.bone.select_head = False
            pbone.bone.select_tail = False
        for i in rev_map:
            name = "bone_"+str(i)
            pb = obj.pose.bones.get(name)
            if pb is None:
                continue
            pb.name = str(rev_map[i]*3)
            pb.bone.select=True
            pb.bone.select_head = True
            pb.bone.select_tail = True
        bpy.ops.pose.group_assign(type=1)
        bone_groups = obj.pose.bone_groups
        bone_groups.active = bone_groups["FETH_bones"]		
        return {'FINISHED'}
		
class OT_FETH_RESET(Operator):
    bl_label = "Reset bones"
    bl_idname = "feth.reset"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        obj = context.object
        map = {}
        rev_map={}
        with open(mytool.my_path) as f:
            u = "default"
            while(u != "sm_"+str(mytool.my_int)):
                u = f.readline().split()[0]		
            while(True):
                a,b = f.readline().split()
                a=int(a)
                b=int(b)
                if a < 0:
                    break
                map[a]=b
                rev_map[b]=a
        for pbone in obj.pose.bones:
            if pbone.name[0]=='b':
                continue
            pbone.name="bone_"+ str(map[int(pbone.name)//3])
        bpy.ops.pose.group_remove()	
        return {'FINISHED'}
		
# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------

class OBJECT_PT_FethPanel(Panel):
    bl_label = "FETH Plugin"
    bl_idname = "OBJECT_PT_FethPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = "Tools"
    bl_context = 'bone'   


    @classmethod
    def poll(self,context):
        return (context.object and context.object.type == 'ARMATURE' and context.object.data.bones.active)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        
        layout.prop(mytool, "my_path")
        layout.prop(mytool, "my_int")        
        layout.operator("feth.rename")
        layout.operator("feth.reset")
        layout.separator()

class OT_FETH_CLEAN_VG(Operator):
    bl_idname = "feth.clean_vg"
    bl_label = "FETH remove extra vg"
    bl_region_type = 'UI'
	
    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH')
		
    def execute(self, context):
        obj = context.object
        obj.update_from_editmode()
        vgs = [vg for vg in obj.vertex_groups if vg.name.split("_")[0]=="bone"]
        while(vgs):
            obj.vertex_groups.remove(vgs.pop())		
        return {'FINISHED'}
def draw_func(self, context):
    self.layout.operator(OT_FETH_CLEAN_VG.bl_idname)
# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    OT_FETH_RENAME,
	OT_FETH_RESET,
    OT_FETH_CLEAN_VG,
    OBJECT_PT_FethPanel
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)
    bpy.types.MESH_MT_vertex_group_context_menu.prepend(draw_func)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool
    bpy.types.MESH_MT_vertex_group_context_menu.remove(draw_func)


if __name__ == "__main__":
    register()