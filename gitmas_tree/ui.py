import bpy
from .func import GITMASTREE_OT_generate

class GITMASTREE_PT_panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gitmas Tree"
    bl_label = "Gitmas Tree"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "gitmas_repo_path", text="Repository")
        layout.prop(scene, "gitmas_commits_count", text="Commit Count")
        layout.operator(GITMASTREE_OT_generate.bl_idname)