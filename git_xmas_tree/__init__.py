bl_info = {
    "name": "Git Xmas Tree",
    "author": "Hiroshi Minakata",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Git Xmas",
    "description": "Visualize git commit history as a 3D Xmas tree",
    "category": "Object",
}

import os
import bpy
from .ui import GITXMASS_PT_panel
from .git_parser import load_commits
from .builder import build_tree

class GITXMASS_OT_generate(bpy.types.Operator):
    bl_idname = "gitxmas.generate"
    bl_label = "Generate"

    def execute(self, context):
        repo_path = context.scene.repo_path
        if not repo_path:
            self.report({'ERROR'}, "Path is empty")
            return {'CANCELLED'}

        if not os.path.isdir(repo_path):
            self.report({'ERROR'}, "Path does not exist")
            return {'CANCELLED'}

        git_path = os.path.join(repo_path, '.git')
        if not os.path.isdir(git_path):
            self.report({'ERROR'}, ".git folder not found in the repository")
            return {'CANCELLED'}

        commits = load_commits(repo_path)
        if not commits:
            self.report({'ERROR'}, "No commits found")
            return {'CANCELLED'}

        build_tree(
            commits,
            max_x=context.scene.tree_max_x,
            max_y=context.scene.tree_max_y,
            max_z=context.scene.tree_max_z,
            branch_spacing=context.scene.tree_branch_spacing,
            commit_spacing=context.scene.tree_commit_spacing,
        )
        self.report({'INFO'}, f"{len(commits)} commits visualized")

        return {'FINISHED'}


def register():
    bpy.types.Scene.repo_path = bpy.props.StringProperty(
        name="Repository Path",
        description="Path to git repository",
        default="",
        subtype='DIR_PATH',
    )
    bpy.types.Scene.tree_max_x = bpy.props.FloatProperty(
        name="Max X",
        description="Maximum X range",
        default=5.0,
        min=0.1,
        max=50.0,
    )
    bpy.types.Scene.tree_max_y = bpy.props.FloatProperty(
        name="Max Y",
        description="Maximum Y range",
        default=5.0,
        min=0.1,
        max=50.0,
    )
    bpy.types.Scene.tree_max_z = bpy.props.FloatProperty(
        name="Max Z",
        description="Maximum Z range (height)",
        default=10.0,
        min=0.1,
        max=50.0,
    )
    bpy.types.Scene.tree_branch_spacing = bpy.props.FloatProperty(
        name="Branch Spacing",
        description="Spacing between branches",
        default=1.0,
        min=0.1,
        max=10.0,
    )
    bpy.types.Scene.tree_commit_spacing = bpy.props.FloatProperty(
        name="Commit Spacing",
        description="Spacing between commits",
        default=1.0,
        min=0.1,
        max=10.0,
    )
    bpy.utils.register_class(GITXMASS_OT_generate)
    bpy.utils.register_class(GITXMASS_PT_panel)


def unregister():
    del bpy.types.Scene.repo_path
    del bpy.types.Scene.tree_max_x
    del bpy.types.Scene.tree_max_y
    del bpy.types.Scene.tree_max_z
    del bpy.types.Scene.tree_branch_spacing
    del bpy.types.Scene.tree_commit_spacing
    bpy.utils.unregister_class(GITXMASS_PT_panel)
    bpy.utils.unregister_class(GITXMASS_OT_generate)
