import math
import bpy
from .git_parser import Commit

def get_pentagon_edge_point(major_radius, angle):
    """5角形の辺上の点を取得（中心から指定された角度方向）"""
    # 5角形の頂点の角度（72度間隔）
    pentagon_angles = [math.radians(72 * i) for i in range(5)]
    
    # 5角形の頂点座標
    vertices = [(major_radius * math.cos(a), major_radius * math.sin(a)) for a in pentagon_angles]
    
    # 角度を0-360度の範囲に正規化
    angle = angle % (2 * math.pi)
    
    # どの辺と交わるかを判定
    for i in range(5):
        v1 = vertices[i]
        v2 = vertices[(i + 1) % 5]
        
        # 辺の角度範囲
        a1 = pentagon_angles[i]
        a2 = pentagon_angles[(i + 1) % 5]
        if a2 < a1:
            a2 += 2 * math.pi
        
        # 角度が辺の範囲内かチェック
        angle_check = angle
        if angle < a1 and a2 > 2 * math.pi:
            angle_check += 2 * math.pi
        
        if a1 <= angle_check <= a2:
            # 中心から角度方向の直線と辺の交点を計算
            # 辺の方程式: P = v1 + t * (v2 - v1)
            # 中心からの直線: P = s * (cos(angle), sin(angle))
            
            dx = v2[0] - v1[0]
            dy = v2[1] - v1[1]
            
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            
            # 交点を求める
            # v1[0] + t * dx = s * cos_a
            # v1[1] + t * dy = s * sin_a
            
            denom = dx * sin_a - dy * cos_a
            if abs(denom) > 1e-10:
                t = (v1[1] * cos_a - v1[0] * sin_a) / denom
                x = v1[0] + t * dx
                y = v1[1] + t * dy
                return (x, y)
    
    # フォールバック：外接円上の点
    return (major_radius * math.cos(angle), major_radius * math.sin(angle))

def generate(commits: list[Commit]):
    positions = {}
    levels = {}
    
    # 各コミットのレベル（世代）を計算
    def calculate_level(commit_hash, current_commits):
        if commit_hash in levels:
            return levels[commit_hash]
        
        commit = next((c for c in current_commits if c.hash == commit_hash), None)
        if not commit or not commit.parents:
            levels[commit_hash] = 0
            return 0
        
        parent_levels = [calculate_level(p, current_commits) for p in commit.parents]
        level = max(parent_levels) + 1 if parent_levels else 0
        levels[commit_hash] = level
        return level
    
    # 全コミットのレベルを計算
    for commit in commits:
        calculate_level(commit.hash, commits)
    
    # レベルごとにコミットをグループ化
    level_commits = {}
    for commit in commits:
        level = levels[commit.hash]
        if level not in level_commits:
            level_commits[level] = []
        level_commits[level].append(commit)
    
    # 位置を割り当て（横: インデックス、縦: レベル）
    # X軸は中央揃え
    for level, level_commit_list in level_commits.items():
        num_commits = len(level_commit_list)
        for i, commit in enumerate(level_commit_list):
            x = (i - (num_commits - 1) / 2) * 3.0
            z = level * 2.5
            positions[commit.hash] = (x, 0, z)
    
    # 各コミットの角度インデックスを計算（親から継承）
    angle_indices = {}
    global_index = [0]  # グローバルカウンター
    
    def assign_angle_index(commit_hash, current_commits):
        if commit_hash in angle_indices:
            return angle_indices[commit_hash]
        
        commit = next((c for c in current_commits if c.hash == commit_hash), None)
        if not commit:
            return 0
        
        # 親がいない場合は新しいインデックスを割り当て
        if not commit.parents:
            angle_indices[commit_hash] = global_index[0]
            global_index[0] += 1
            return angle_indices[commit_hash]
        
        # 親のインデックスを取得（複数の親がいる場合は最初の親）
        parent_hash = commit.parents[0]
        parent_index = assign_angle_index(parent_hash, current_commits)
        
        # 親のインデックスの次を使用
        angle_indices[commit_hash] = global_index[0]
        global_index[0] += 1
        return angle_indices[commit_hash]
    
    # 全コミットの角度インデックスを計算
    for commit in commits:
        assign_angle_index(commit.hash, commits)
    
    # ノード（球+トーラス）を作成
    created_torus = set()  # 作成済みトーラスを記録 (z座標, major_radius)
    
    for commit in commits:
        if commit.hash not in positions:
            continue
        pos = positions[commit.hash]
        level = levels[commit.hash]
        
        # 角度インデックスを取得
        index = angle_indices[commit.hash]
        
        # 球の半径
        sphere_radius = 0.5
        
        # トーラスの半径を計算
        major_radius = abs(pos[0])
        
        # 45度間隔で角度を決定
        angle = math.radians(45 * index)
        
        # 5角形の辺上の点を取得（回転なし）
        sphere_x_base, sphere_y_base = get_pentagon_edge_point(major_radius, angle)
        
        # トーラスの回転角度を適用
        rotation_angle = math.radians(45 * level)
        cos_rot = math.cos(rotation_angle)
        sin_rot = math.sin(rotation_angle)
        sphere_x = sphere_x_base * cos_rot - sphere_y_base * sin_rot
        sphere_y = sphere_x_base * sin_rot + sphere_y_base * cos_rot
        sphere_pos = (sphere_x, sphere_y, pos[2])
        
        # 球を作成（オーナメント）
        bpy.ops.mesh.primitive_uv_sphere_add(radius=sphere_radius, location=sphere_pos)
        sphere = bpy.context.active_object
        sphere.name = f"Commit_Sphere_{commit.hash[:7]}"
        
        # オーナメントのマテリアルを作成
        mat = bpy.data.materials.new(name=f"Ornament_{commit.hash[:7]}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # Principled BSDFノードを追加
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        
        # カラフルなオーナメント色（コミットハッシュから色を生成）
        hash_int = int(commit.hash[:6], 16)
        r = ((hash_int >> 16) & 0xFF) / 255.0
        g = ((hash_int >> 8) & 0xFF) / 255.0
        b = (hash_int & 0xFF) / 255.0
        bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.8
        bsdf.inputs['Roughness'].default_value = 0.2
        
        # マテリアル出力ノード
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (200, 0)
        
        # ノードを接続
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        # 球にマテリアルを適用
        sphere.data.materials.append(mat)
        
        # トーラスを作成（X=0の位置に配置、外周が球の位置に来るように）
        # major_radiusは球までの距離
        # minor_radiusは管の太さ
        minor_radius = 0.3
        
        # トーラスの中心はX=0, Y=0, Z座標は球と同じ
        torus_pos = (0, 0, pos[2])
        torus_key = (pos[2], major_radius)
        
        # major_radiusが0より大きく、まだ作成されていない場合のみトーラスを作成
        if major_radius > 0 and torus_key not in created_torus:
            bpy.ops.mesh.primitive_torus_add(
                major_radius=major_radius,
                minor_radius=minor_radius,
                location=torus_pos,
                major_segments=5,  # 5角形に変更
                minor_segments=3
            )
            torus = bpy.context.active_object
            torus.name = f"Commit_Torus_{commit.hash[:7]}"
            
            # 世代ごとに45度回転
            torus.rotation_euler[2] = math.radians(45 * level)
            
            # 葉のマテリアルを作成
            leaf_mat = bpy.data.materials.new(name=f"Leaf_{commit.hash[:7]}")
            leaf_mat.use_nodes = True
            leaf_nodes = leaf_mat.node_tree.nodes
            leaf_nodes.clear()
            
            # Principled BSDFノードを追加
            leaf_bsdf = leaf_nodes.new(type='ShaderNodeBsdfPrincipled')
            leaf_bsdf.location = (0, 0)
            
            # 緑色の葉
            leaf_bsdf.inputs['Base Color'].default_value = (0.1, 0.6, 0.2, 1.0)
            leaf_bsdf.inputs['Roughness'].default_value = 0.7
            
            # マテリアル出力ノード
            leaf_output = leaf_nodes.new(type='ShaderNodeOutputMaterial')
            leaf_output.location = (200, 0)
            
            # ノードを接続
            leaf_mat.node_tree.links.new(leaf_bsdf.outputs['BSDF'], leaf_output.inputs['Surface'])
            
            # トーラスにマテリアルを適用
            torus.data.materials.append(leaf_mat)
            
            created_torus.add(torus_key)
        
        # テキストを追加（球の位置に合わせる）
        bpy.ops.object.text_add(location=(sphere_pos[0], sphere_pos[1], sphere_pos[2] + 0.5))
        text = bpy.context.active_object
        text.data.body = commit.message
        text.data.size = 0.3
        text.data.align_x = 'CENTER'
        text.name = f"Text_{commit.hash[:7]}"
        text.rotation_euler[0] = math.pi / 2
    
    # 中央に幹を追加
    if positions:
        # 最小・最大のZ座標を取得
        z_coords = [pos[2] for pos in positions.values()]
        min_z = min(z_coords)
        max_z = max(z_coords)
        
        # 下に2世代分伸ばす
        trunk_bottom_z = min_z - 2 * 2.5
        trunk_height = max_z - trunk_bottom_z
        trunk_center_z = (trunk_bottom_z + max_z) / 2
        
        # 円錐で幹を作成（下が太く上が細い）
        bpy.ops.mesh.primitive_cone_add(
            radius1=0.5,  # 底面の半径
            radius2=0.15,  # 上面の半径
            depth=trunk_height,
            location=(0, 0, trunk_center_z)
        )
        trunk = bpy.context.active_object
        trunk.name = "Tree_Trunk"
        
        # 幹のマテリアルを作成（枝よりダークブラウン）
        trunk_mat = bpy.data.materials.new(name="Trunk_Material")
        trunk_mat.use_nodes = True
        trunk_nodes = trunk_mat.node_tree.nodes
        trunk_nodes.clear()
        
        # Principled BSDFノードを追加
        trunk_bsdf = trunk_nodes.new(type='ShaderNodeBsdfPrincipled')
        trunk_bsdf.location = (0, 0)
        
        # ダークブラウン（枝より暗い）
        trunk_bsdf.inputs['Base Color'].default_value = (0.25, 0.15, 0.05, 1.0)
        trunk_bsdf.inputs['Roughness'].default_value = 0.9
        
        # マテリアル出力ノード
        trunk_output = trunk_nodes.new(type='ShaderNodeOutputMaterial')
        trunk_output.location = (200, 0)
        
        # ノードを接続
        trunk_mat.node_tree.links.new(trunk_bsdf.outputs['BSDF'], trunk_output.inputs['Surface'])
        
        # 幹にマテリアルを適用
        trunk.data.materials.append(trunk_mat)
    
    # 親子関係を線で結ぶ
    for commit in commits:
        if commit.hash not in positions:
            continue
        
        # 子の位置を計算
        pos = positions[commit.hash]
        index = angle_indices[commit.hash]
        level = levels[commit.hash]
        major_radius = abs(pos[0])
        angle = math.radians(45 * index)
        child_x_base, child_y_base = get_pentagon_edge_point(major_radius, angle)
        
        # トーラスの回転角度を適用
        rotation_angle = math.radians(45 * level)
        cos_rot = math.cos(rotation_angle)
        sin_rot = math.sin(rotation_angle)
        child_x = child_x_base * cos_rot - child_y_base * sin_rot
        child_y = child_x_base * sin_rot + child_y_base * cos_rot
        child_pos = (child_x, child_y, pos[2])
        
        for parent_hash in commit.parents:
            if parent_hash not in positions:
                continue
            
            # 親の位置を計算
            parent_pos_orig = positions[parent_hash]
            parent_index = angle_indices[parent_hash]
            parent_level = levels[parent_hash]
            parent_major_radius = abs(parent_pos_orig[0])
            parent_angle = math.radians(45 * parent_index)
            parent_x_base, parent_y_base = get_pentagon_edge_point(parent_major_radius, parent_angle)
            
            # トーラスの回転角度を適用
            parent_rotation_angle = math.radians(45 * parent_level)
            parent_cos_rot = math.cos(parent_rotation_angle)
            parent_sin_rot = math.sin(parent_rotation_angle)
            parent_x = parent_x_base * parent_cos_rot - parent_y_base * parent_sin_rot
            parent_y = parent_x_base * parent_sin_rot + parent_y_base * parent_cos_rot
            parent_pos = (parent_x, parent_y, parent_pos_orig[2])
            
            curve_data = bpy.data.curves.new(name=f"Edge_{commit.hash[:7]}_to_{parent_hash[:7]}", type='CURVE')
            curve_data.dimensions = '3D'
            curve_data.bevel_depth = 0.15
            
            polyline = curve_data.splines.new('POLY')
            polyline.points.add(1)
            polyline.points[0].co = (child_pos[0], child_pos[1], child_pos[2], 1)
            polyline.points[1].co = (parent_pos[0], parent_pos[1], parent_pos[2], 1)
            
            curve_obj = bpy.data.objects.new(f"Edge_{commit.hash[:7]}", curve_data)
            bpy.context.collection.objects.link(curve_obj)
            
            # 枝のマテリアルを作成
            branch_mat = bpy.data.materials.new(name=f"Branch_{commit.hash[:7]}")
            branch_mat.use_nodes = True
            branch_nodes = branch_mat.node_tree.nodes
            branch_nodes.clear()
            
            # Principled BSDFノードを追加
            branch_bsdf = branch_nodes.new(type='ShaderNodeBsdfPrincipled')
            branch_bsdf.location = (0, 0)
            
            # 茶色の枝
            branch_bsdf.inputs['Base Color'].default_value = (0.4, 0.25, 0.1, 1.0)
            branch_bsdf.inputs['Roughness'].default_value = 0.8
            
            # マテリアル出力ノード
            branch_output = branch_nodes.new(type='ShaderNodeOutputMaterial')
            branch_output.location = (200, 0)
            
            # ノードを接続
            branch_mat.node_tree.links.new(branch_bsdf.outputs['BSDF'], branch_output.inputs['Surface'])
            
            # カーブにマテリアルを適用
            curve_obj.data.materials.append(branch_mat)

    