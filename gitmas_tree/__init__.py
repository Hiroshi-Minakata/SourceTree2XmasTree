import pathlib
import tomllib
import bpy
from .func import GITMASTREE_OT_generate
from .ui import GITMASTREE_PT_panel

PACKAGE_PATH = pathlib.Path(__file__).parent
MANIFEST_PATH = PACKAGE_PATH / "blender_manifest.toml"
manifest = tomllib.loads(MANIFEST_PATH.read_text())

classes = [
    GITMASTREE_PT_panel,
    GITMASTREE_OT_generate,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.gitmas_repo_path = bpy.props.StringProperty(
        name="リポジトリパス",
        description="Gitリポジトリのパスを指定します",
        subtype="DIR_PATH"
    )
    bpy.types.Scene.gitmas_commits_count = bpy.props.IntProperty(
        name="コミット数",
        description="ツリーに使用するコミットの数(0~500)",
        default=100,
        min=0,
        max=500
    )

def unregister():
    del bpy.types.Scene.gitmas_repo_path
    del bpy.types.Scene.gitmas_commits_count

    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
