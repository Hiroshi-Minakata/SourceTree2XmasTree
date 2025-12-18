import bpy

class GITXMASS_PT_panel(bpy.types.Panel):
    bl_label = "Git Xmas Tree"
    bl_idname = "GITXMASS_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Git Xmas'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        
        # リポジトリパス
        layout.prop(scene, "repo_path")
        
        # レイアウト設定
        box = layout.box()
        box.label(text="Layout Settings:", icon='PREFERENCES')
        box.prop(scene, "tree_max_x")
        box.prop(scene, "tree_max_y")
        box.prop(scene, "tree_max_z")
        box.prop(scene, "tree_branch_spacing")
        box.prop(scene, "tree_commit_spacing")
        
        # 生成ボタン
        layout.operator("gitxmas.generate", icon="OUTLINER_OB_GROUP_INSTANCE")
