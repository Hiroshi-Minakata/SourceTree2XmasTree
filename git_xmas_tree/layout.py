import math
import random


class TreeLayout:
    def __init__(
        self,
        commits,
        height=6.0,
        base_radius=2.0,
        radius_power=0.75,
        seed=0,
    ):
        self.commits = commits
        self.height = height
        self.base_radius = base_radius
        self.radius_power = radius_power

        random.seed(seed)
        self._normalize_time()

    def _normalize_time(self):
        times = [c.time for c in self.commits]
        self.t_min = min(times)
        self.t_max = max(times)
        self.t_range = max(1, self.t_max - self.t_min)

    def position(self, commit, index):
        z_norm = (commit.time - self.t_min) / self.t_range
        z = z_norm * self.height

        r_max = (1.0 - z_norm) ** self.radius_power * self.base_radius

        h = int(commit.hash[:8], 16)
        angle = (h % 360) * math.pi / 180.0

        r = max(0.0, r_max + random.uniform(-0.15, 0.15))

        x = r * math.cos(angle)
        y = r * math.sin(angle)

        return (x, y, z)


class BranchLayout:
    """純粋なブランチ構造レイアウト"""
    def __init__(
        self,
        commits,
        branch_spacing=1,
        commit_spacing=1,
        max_x=5.0,
        max_y=5.0,
        max_z=10.0,
    ):
        self.commits = commits
        self.branch_spacing = branch_spacing
        self.commit_spacing = commit_spacing
        self.max_x = max_x
        self.max_y = max_y
        self.max_z = max_z
        self._calculate_branch_positions()
        self._calculate_bounds()
    
    def _calculate_branch_positions(self):
        """各コミットのブランチレーンと深さを計算"""
        self.commit_lanes = {}
        self.commit_depths = {}
        self.used_lanes = set()
        
        # まず深さを計算（親からの距離）
        commit_map = {c.hash: c for c in self.commits}
        
        def calculate_depth(commit_hash, visited=None):
            if visited is None:
                visited = set()
            if commit_hash in self.commit_depths:
                return self.commit_depths[commit_hash]
            if commit_hash in visited:
                return 0
            if commit_hash not in commit_map:
                return 0
                
            visited.add(commit_hash)
            commit = commit_map[commit_hash]
            
            if not commit.parents:
                depth = 0
            else:
                parent_depths = [calculate_depth(p, visited.copy()) for p in commit.parents if p in commit_map]
                depth = max(parent_depths) + 1 if parent_depths else 0
            
            self.commit_depths[commit_hash] = depth
            return depth
        
        for commit in self.commits:
            calculate_depth(commit.hash)
        
        # 親→子のマッピングを作成
        parent_to_children = {}
        for commit in self.commits:
            for parent_hash in commit.parents:
                if parent_hash in commit_map:
                    if parent_hash not in parent_to_children:
                        parent_to_children[parent_hash] = []
                    parent_to_children[parent_hash].append(commit.hash)
        
        # ルートコミット（親なし）を中央（X=0）に配置
        root_commits = [c for c in self.commits if not c.parents or not any(p in commit_map for p in c.parents)]
        for root in root_commits:
            self.commit_lanes[root.hash] = 0.0
            self.used_lanes.add(0.0)
        
        # 深さ順にコミットを処理（親→子の順）
        commits_by_depth = sorted(self.commits, key=lambda c: self.commit_depths.get(c.hash, 0))
        
        for commit in commits_by_depth:
            if commit.hash in self.commit_lanes:
                # すでに配置済み
                parent_lane = self.commit_lanes[commit.hash]
            else:
                # 最初の親のレーンを使用
                if commit.parents and commit.parents[0] in self.commit_lanes:
                    parent_lane = self.commit_lanes[commit.parents[0]]
                else:
                    parent_lane = 0.0
                self.commit_lanes[commit.hash] = parent_lane
            
            # この親から派生する子コミットを中央揃えで配置
            if commit.hash in parent_to_children:
                children = parent_to_children[commit.hash]
                num_children = len(children)
                
                if num_children == 1:
                    # 子が1つ: 親と同じ位置
                    self.commit_lanes[children[0]] = parent_lane
                else:
                    # 子が複数: 親を中心に左右対称に配置
                    for i, child_hash in enumerate(children):
                        offset = (i - (num_children - 1) / 2.0) * self.branch_spacing
                        self.commit_lanes[child_hash] = parent_lane + offset
                        self.used_lanes.add(parent_lane + offset)
    
    def _calculate_bounds(self):
        """全コミットの座標を仮計算して境界を求める"""
        temp_positions = []
        for i, commit in enumerate(self.commits):
            pos = self._position_raw(commit, i)
            temp_positions.append(pos)
        
        if not temp_positions:
            self.scale = 1.0
            self.offset_x = 0.0
            self.offset_y = 0.0
            self.offset_z = 0.0
            return
        
        # 最小・最大を計算
        xs = [p[0] for p in temp_positions]
        ys = [p[1] for p in temp_positions]
        zs = [p[2] for p in temp_positions]
        
        min_x, max_x_actual = min(xs), max(xs)
        min_y, max_y_actual = min(ys), max(ys)
        min_z, max_z_actual = min(zs), max(zs)
        
        # 実際の範囲
        range_x = max_x_actual - min_x
        range_y = max_y_actual - min_y
        range_z = max_z_actual - min_z
        
        # スケーリング係数を計算（範囲が0の場合は1.0）
        scale_x = (self.max_x * 2) / range_x if range_x > 0 else 1.0
        scale_y = (self.max_y * 2) / range_y if range_y > 0 else 1.0
        scale_z = self.max_z / range_z if range_z > 0 else 1.0
        
        # 最小スケールを使用（アスペクト比を維持）
        self.scale = min(scale_x, scale_y, scale_z)
        
        # オフセット - XY方向は中心化しない（lane=0が原点にあるため）
        # Z軸のみ最小値を0にする
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = min_z
    
    def position(self, commit, index):
        """スケーリングと正規化を適用した最終的な3D座標を返す"""
        x, y, z = self._position_raw(commit, index)
        
        # 中心化とスケーリング
        x = (x - self.offset_x) * self.scale
        y = (y - self.offset_y) * self.scale
        z = (z - self.offset_z) * self.scale
        
        return (x, y, z)
    
    def _position_raw(self, commit, index):
        """スケーリング前の生の座標を返す"""
        # Z軸: 高さ（深さに基づく）- 反転させる
        depth = self.commit_depths.get(commit.hash, index)
        max_depth = max(self.commit_depths.values()) if self.commit_depths else 1
        z = (max_depth - depth) * self.commit_spacing  # 反転: 深いコミットほど下に
        
        # X, Y軸: レーンを中心軸の周りに円形配置（円錐形）
        lane = self.commit_lanes.get(commit.hash, 0)
        
        # 半径を深さに応じて変化（深いほど大きく）
        depth_ratio = depth / max_depth if max_depth > 0 else 0
        base_spacing = self.branch_spacing * (1 + depth_ratio * 2)  # 下に行くほど広がる
        
        if lane == 0:
            # 中央のブランチは原点
            x = 0.0
            y = 0.0
        else:
            # レーンに基づいて角度を計算（各レーンを均等に配置）
            # 正のレーンと負のレーンで異なる角度に
            angle = lane * (2 * math.pi / 8)  # 8レーンで1周するように
            radius = abs(lane) * base_spacing
            
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
        
        return (x, y, z)
