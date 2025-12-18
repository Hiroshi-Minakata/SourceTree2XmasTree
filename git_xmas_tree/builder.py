import bpy
import random
import math
from .layout import BranchLayout
from .materials import (
    create_branch_material,
    create_trunk_material,
    create_ornament_material,
    create_light_material,
    create_star_material,
    create_commit_material,
)


def build_tree(commits, max_x=5.0, max_y=5.0, max_z=10.0, branch_spacing=1.0, commit_spacing=1.0):
    layout = BranchLayout(
        commits,
        branch_spacing=branch_spacing,
        commit_spacing=commit_spacing,
        max_x=max_x,
        max_y=max_y,
        max_z=max_z,
    )
    positions = {}
    
    # マテリアルを作成
    branch_mat = create_branch_material()
    trunk_mat = create_trunk_material()
    ornament_colors = ['red', 'gold', 'blue', 'silver', 'purple', 'green']
    ornament_mats = {color: create_ornament_material(color) for color in ornament_colors}
    light_mat = create_light_material()
    star_mat = create_star_material()

    # コミット（球）
    commit_objects = []
    for i, c in enumerate(commits):
        pos = layout.position(c, i)
        positions[c.hash] = pos

        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.18,
            location=pos,
        )
        # 球の名前をコミットメッセージに設定
        obj = bpy.context.active_object
        obj.name = c.message if c.message else c.hash[:7]
        
        # コミットにマテリアルを適用
        commit_mat = create_commit_material(c.branch)
        obj.data.materials.append(commit_mat)
        commit_objects.append(obj)

    # 枝（親子）
    for c in commits:
        for p in c.parents:
            if p in positions:
                branch_obj = _make_branch(positions[p], positions[c.hash], c.branch)
                if branch_obj:
                    branch_obj.data.materials.append(branch_mat)
    
    # 幹を追加
    # 実際のコミット位置から高さを計算
    if positions:
        z_coords = [pos[2] for pos in positions.values()]
        min_z = min(z_coords)
        max_z = max(z_coords)
        trunk_height = max_z - min_z + 1.0  # 少し余裕を持たせる
        trunk_center_z = (min_z + max_z) / 2
    else:
        trunk_height = 2.0
        trunk_center_z = 0.0
    
    trunk_radius = 0.15
    bpy.ops.mesh.primitive_cylinder_add(
        radius=trunk_radius,
        depth=trunk_height,
        location=(0, 0, trunk_center_z)
    )
    trunk = bpy.context.active_object
    trunk.name = "Trunk"
    trunk.data.materials.append(trunk_mat)
    
    # 他のブランチから幹に枝を繋げる
    for c in commits:
        lane = layout.commit_lanes.get(c.hash, 0)
        if lane != 0:  # 中央以外のブランチ
            pos = positions[c.hash]
            # 幹の表面への接続点（球より下から上に角度をつけて伸びる）
            # 球の位置に対して下方向にオフセットを付ける
            z_offset = 0.5  # 枝の角度を調整する値（大きいほど急角度）
            trunk_surface_pos = (trunk_radius, 0, pos[2] - z_offset)
            trunk_branch_obj = _make_branch(trunk_surface_pos, pos, c.branch, radius=0.02)
            if trunk_branch_obj:
                trunk_branch_obj.data.materials.append(branch_mat)
    
    # オーナメントを追加（コミットの一部をランダムに選択）
    num_ornaments = min(len(commits) // 3, 30)  # コミット数の1/3、最大30個
    ornament_indices = random.sample(range(len(commits)), num_ornaments)
    for idx in ornament_indices:
        pos = positions[commits[idx].hash]
        # コミットの少し下にオーナメントを配置
        ornament_pos = (pos[0], pos[1], pos[2] - 0.3)
        color = random.choice(ornament_colors)
        
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.12,
            location=ornament_pos,
        )
        ornament = bpy.context.active_object
        ornament.name = f"Ornament_{color}"
        ornament.data.materials.append(ornament_mats[color])
    
    # ライトを追加（螺旋状に配置）
    num_lights = 20
    for i in range(num_lights):
        t = i / num_lights
        z = t * trunk_height + min_z
        angle = t * 6 * math.pi  # 3回転
        radius = (1 - t) * max_x * 0.8
        
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.08,
            location=(x, y, z)
        )
        light = bpy.context.active_object
        light.name = f"Light_{i}"
        light.data.materials.append(light_mat)
    
    # 頂上に星を追加
    if positions:
        z_coords = [pos[2] for pos in positions.values()]
        top_z = max(z_coords) + 0.5
    else:
        top_z = trunk_height / 2 + 0.5
    
    # 星の形状を作成（円錐を複数組み合わせて星型に）
    bpy.ops.mesh.primitive_cone_add(
        radius1=0.3,
        depth=0.6,
        location=(0, 0, top_z)
    )
    star = bpy.context.active_object
    star.name = "Star"
    star.data.materials.append(star_mat)
    
    # ポイントライトを星の位置に追加（輝きを強調）
    bpy.ops.object.light_add(type='POINT', location=(0, 0, top_z))
    star_light = bpy.context.active_object
    star_light.name = "StarLight"
    star_light.data.energy = 500
    star_light.data.color = (1.0, 0.9, 0.3)


def _make_branch(p1, p2, branch_name="", radius=0.03):
    curve = bpy.data.curves.new("BranchCurve", type="CURVE")
    curve.dimensions = '3D'

    spline = curve.splines.new("POLY")
    spline.points.add(1)

    spline.points[0].co = (*p1, 1)
    spline.points[1].co = (*p2, 1)

    curve.bevel_depth = radius
    curve.bevel_resolution = 3

    # 枝の名前をブランチ名に設定
    obj_name = branch_name if branch_name else "Branch"
    obj = bpy.data.objects.new(obj_name, curve)
    bpy.context.collection.objects.link(obj)
    
    return obj
