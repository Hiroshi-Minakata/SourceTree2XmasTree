import bpy


def create_branch_material():
    """緑色の枝のマテリアル"""
    mat = bpy.data.materials.new(name="BranchMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.1, 0.4, 0.1, 1.0)  # 深緑
    bsdf.inputs['Roughness'].default_value = 0.7
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_trunk_material():
    """茶色の幹のマテリアル"""
    mat = bpy.data.materials.new(name="TrunkMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.3, 0.15, 0.05, 1.0)  # 茶色
    bsdf.inputs['Roughness'].default_value = 0.9
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_ornament_material(color):
    """カラフルなオーナメントのマテリアル（光沢あり）"""
    mat = bpy.data.materials.new(name=f"OrnamentMaterial_{color}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    # 色のバリエーション
    colors = {
        'red': (0.8, 0.1, 0.1, 1.0),
        'gold': (0.9, 0.7, 0.1, 1.0),
        'blue': (0.1, 0.3, 0.8, 1.0),
        'silver': (0.7, 0.7, 0.8, 1.0),
        'purple': (0.6, 0.1, 0.6, 1.0),
        'green': (0.1, 0.7, 0.2, 1.0),
    }
    
    bsdf.inputs['Base Color'].default_value = colors.get(color, (0.8, 0.1, 0.1, 1.0))
    bsdf.inputs['Metallic'].default_value = 0.8
    bsdf.inputs['Roughness'].default_value = 0.2
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_light_material():
    """光るライトのマテリアル（エミッション）"""
    mat = bpy.data.materials.new(name="LightMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1.0, 0.9, 0.5, 1.0)  # 暖かい黄色
    emission.inputs['Strength'].default_value = 5.0
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    return mat


def create_star_material():
    """星のマテリアル（金色に輝く）"""
    mat = bpy.data.materials.new(name="StarMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1.0, 0.9, 0.3, 1.0)  # 金色
    emission.inputs['Strength'].default_value = 8.0
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (1.0, 0.8, 0.2, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.1
    
    mix = nodes.new(type='ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.5
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(emission.outputs['Emission'], mix.inputs[1])
    mat.node_tree.links.new(bsdf.outputs['BSDF'], mix.inputs[2])
    mat.node_tree.links.new(mix.outputs['Shader'], output.inputs['Surface'])
    
    return mat


def create_commit_material(branch_name=""):
    """コミット用のマテリアル（ブランチごとに色を変える）"""
    mat = bpy.data.materials.new(name=f"CommitMaterial_{branch_name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    # ブランチ名のハッシュから色を生成
    if branch_name:
        hash_val = hash(branch_name)
        r = ((hash_val & 0xFF) / 255.0) * 0.6 + 0.3
        g = (((hash_val >> 8) & 0xFF) / 255.0) * 0.6 + 0.3
        b = (((hash_val >> 16) & 0xFF) / 255.0) * 0.6 + 0.3
    else:
        r, g, b = 0.5, 0.5, 0.5
    
    bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.3
    bsdf.inputs['Roughness'].default_value = 0.4
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat
