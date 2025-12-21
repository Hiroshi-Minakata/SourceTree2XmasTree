import os
import bpy
from . import git_parser
from . import tree_generator

class GITMASTREE_OT_generate(bpy.types.Operator):
    bl_idname = "gitmastree.generate"
    bl_label = "Generate"
    bl_description = "Git履歴からクリスマスツリーを生成します"

    def execute(self, context):
        repo_path = context.scene.gitmas_repo_path
        if not os.path.exists(repo_path):
            self.report({"ERROR"}, f"パスが存在しません: {repo_path}")
            return {"CANCELLED"}
        if not os.path.isdir(repo_path):
            self.report({"ERROR"}, f"ディレクトリではありません: {repo_path}")
            return {"CANCELLED"}
        if not os.path.isdir(os.path.join(repo_path, ".git")):
            self.report({"ERROR"}, f"Gitリポジトリではありません: {repo_path}")
            return {"CANCELLED"}

        commit_count = context.scene.gitmas_commits_count
        commits = git_parser.load_commits(repo_path, commit_count)
        tree_generator.generate(commits)

        self.report({"INFO"}, f"{commits}")
        return {"FINISHED"}