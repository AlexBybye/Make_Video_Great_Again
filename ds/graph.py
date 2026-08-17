# ds/graph.py — 自定义图 (邻接表实现)
# 用于用户-视频二分图, BFS 找相似用户/推荐路径

from collections import deque


class Graph:
    """
    邻接表实现的有权/无权图。
    支持 BFS/DFS 遍历, 用于用户-视频二分图分析。
    每个顶点存储 (neighbor, weight) 的边列表。
    """

    def __init__(self, directed=False):
        self.adj = {}          # vertex -> list of (neighbor, weight)
        self.directed = directed

    def add_vertex(self, v):
        if v not in self.adj:
            self.adj[v] = []

    def add_edge(self, u, v, weight=1.0):
        """添加边 u->v (有权重), 若为无向图则同时添加 v->u"""
        self.add_vertex(u)
        self.add_vertex(v)
        self.adj[u].append((v, weight))
        if not self.directed:
            self.adj[v].append((u, weight))

    def neighbors(self, v):
        """返回顶点 v 的所有邻居 [(neighbor, weight), ...]"""
        return self.adj.get(v, [])

    def degree(self, v):
        return len(self.adj.get(v, []))

    def vertices(self):
        return list(self.adj.keys())

    def vertex_count(self):
        return len(self.adj)

    def edge_count(self):
        total = sum(len(edges) for edges in self.adj.values())
        return total if self.directed else total // 2

    def bfs(self, start, max_depth=None):
        """
        广度优先搜索, 返回 (visited_set, distances_dict)。
        max_depth 限制搜索深度。
        """
        visited = set()
        distances = {}
        queue = deque()
        queue.append((start, 0))
        visited.add(start)
        distances[start] = 0

        while queue:
            v, dist = queue.popleft()
            if max_depth is not None and dist >= max_depth:
                continue
            for neighbor, weight in self.adj.get(v, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[neighbor] = dist + 1
                    queue.append((neighbor, dist + 1))

        return visited, distances

    def dfs(self, start, visited=None):
        """深度优先搜索, 返回访问过的顶点集合"""
        if visited is None:
            visited = set()
        visited.add(start)
        for neighbor, weight in self.adj.get(start, []):
            if neighbor not in visited:
                self.dfs(neighbor, visited)
        return visited

    def bfs_with_parent(self, start, max_depth=None):
        """
        BFS 带父节点跟踪, 用于路径回溯。
        返回 (parent_dict, distances_dict)。
        parent[v] = 从 start 到 v 的路径上 v 的前驱节点。
        """
        parent = {start: None}
        distances = {start: 0}
        queue = deque([start])

        while queue:
            v = queue.popleft()
            dist = distances[v]
            if max_depth is not None and dist >= max_depth:
                continue
            for neighbor, weight in self.adj.get(v, []):
                if neighbor not in distances:
                    distances[neighbor] = dist + 1
                    parent[neighbor] = v
                    queue.append(neighbor)

        return parent, distances

    def reconstruct_path(self, parent, target):
        """从 parent 字典回溯路径 [start, ..., target]"""
        if target not in parent:
            return None
        path = []
        cur = target
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()
        return path

    def shortest_path(self, u, v):
        """BFS 求最短路径 (无权), 返回路径列表"""
        if u not in self.adj or v not in self.adj:
            return None
        parent = {u: None}
        queue = deque([u])
        while queue:
            cur = queue.popleft()
            if cur == v:
                break
            for neighbor, weight in self.adj.get(cur, []):
                if neighbor not in parent:
                    parent[neighbor] = cur
                    queue.append(neighbor)
        if v not in parent:
            return None
        path = []
        cur = v
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()
        return path

    def connected_components(self):
        """返回所有连通分量 (用于无向图)"""
        all_visited = set()
        components = []
        for v in self.adj:
            if v not in all_visited:
                comp = self.dfs(v)
                all_visited.update(comp)
                components.append(comp)
        return components

    def __repr__(self):
        return f"Graph(vertices={len(self.adj)}, edges={self.edge_count()}, directed={self.directed})"
