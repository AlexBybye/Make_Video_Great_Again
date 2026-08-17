# ds/data_store.py — 统一数据存储层
# 利用 DataCache 的 pandas DataFrame (已在内存) 构建自建数据结构
# 避免重复读 CSV, 提升启动速度

import csv
import os
from ds.hash_map import HashMap
from ds.graph import Graph
from ds.sparse_matrix import CSRSparseMatrix
from ds.max_heap import MaxHeap
from ds.segment_tree import SegmentTree
from ds.trie import Trie
from ds.lru_cache import LRUCache


class DataStore:
    """
    统一数据存储 — 单例模式。
    从 pandas DataFrame 构建自建数据结构, 提供 O(1)/O(log n) 的高效查询。
    """

    _instance = None
    BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _csv_path(self, name):
        return os.path.join(self.BASE_DIR, 'data', f'{name}.csv')

    def _ensure_init(self):
        if not self._initialized:
            self.init()

    def init(self, users_df=None, videos_df=None, operations_df=None):
        """
        从 pandas DataFrame 构建所有自建数据结构。
        若未传入 DataFrame, 则从 data_cache 回退加载。
        """
        if self._initialized:
            return

        print("[DataStore] 开始构建自建数据结构...")

        # 若未传入, 尝试从 data_cache 获取
        if users_df is None or videos_df is None or operations_df is None:
            from data_cache import DataCache
            DataCache.preload_all()
            users_df = DataCache.load_users()
            videos_df = DataCache.load_videos()
            operations_df = DataCache.load_operations()

        t_start = __import__('time').time()

        # ---------- Step 1: HashMap 层 (O(1) 查询) ----------
        self._load_users(users_df)
        self._load_videos(videos_df)
        self._load_operations(operations_df)

        # ---------- Step 2: Graph 层 ----------
        self._build_user_video_graph()

        # ---------- Step 3: CSR 稀疏矩阵 ----------
        self._build_user_tag_matrix()

        # ---------- Step 4: Trie ----------
        self._build_tag_trie()

        # ---------- Step 5: SegmentTree ----------
        self._build_daily_views_tree()

        # ---------- Step 6: LRU Cache ----------
        self.similar_users_cache = LRUCache(capacity=200)
        self.recommend_cache = LRUCache(capacity=200)

        self._initialized = True
        elapsed = __import__('time').time() - t_start
        print(f"[DataStore] 所有数据结构初始化完成 ({elapsed:.2f}s)")
        self._print_stats()

    # ================================================================
    # 内部构建方法 — 直接用 DataFrame 列
    # ================================================================

    def _load_users(self, df):
        self.users_map = HashMap(initial_capacity=len(df) * 2)
        # 兼容不同列名
        id_col = 'id' if 'id' in df.columns else 'user_id'
        for _, row in df.iterrows():
            uid = int(row[id_col])
            self.users_map.put(uid, {
                'id': uid,
                'age': str(row.get('age', '')),
                'gender': str(row.get('gender', '')),
            })
        print(f"  [HashMap] users: {len(self.users_map)} 条")

    def _load_videos(self, df):
        self.videos_map = HashMap(initial_capacity=len(df) * 2)
        for _, row in df.iterrows():
            vid = int(row['id'])
            self.videos_map.put(vid, {
                'id': vid,
                'tag': str(row.get('tag', '')),
                'views': int(row.get('views', 0)),
                'likes': int(row.get('likes', 0)),
                'title': str(row.get('title', '')),
            })
        print(f"  [HashMap] videos: {len(self.videos_map)} 条")

    def _load_operations(self, df):
        self.operations_list = []
        self.ops_by_user = HashMap(initial_capacity=len(df) // 20)
        self.ops_by_video = HashMap(initial_capacity=len(df) // 5)

        for _, row in df.iterrows():
            uid = int(row['user_id'])
            vid = int(row['video_id'])
            op = {
                'user_id': uid,
                'video_id': vid,
                'liked': int(row.get('liked', 0)),
                'day': int(row.get('day', 1)),
            }
            self.operations_list.append(op)

            ulist = self.ops_by_user.get(uid)
            if ulist is None:
                ulist = []
                self.ops_by_user.put(uid, ulist)
            ulist.append(op)

            vlist = self.ops_by_video.get(vid)
            if vlist is None:
                vlist = []
                self.ops_by_video.put(vid, vlist)
            vlist.append(op)

        print(f"  [HashMap] operations: {len(self.operations_list)} 条")
        print(f"  [HashMap] ops_by_user: {len(self.ops_by_user)} users")
        print(f"  [HashMap] ops_by_video: {len(self.ops_by_video)} videos")

    def _build_user_video_graph(self):
        self.user_video_graph = Graph(directed=False)
        # 直接添加边, 不做重复检查 (相同 pair 多次交互体现为多条并行边, BFS 仍正确)
        for op in self.operations_list:
            u_node = f"U{op['user_id']}"
            v_node = f"V{op['video_id']}"
            weight = 2.0 if op['liked'] == 1 else 1.0
            self.user_video_graph.add_edge(u_node, v_node, weight)
        print(f"  [Graph] user_video_graph: {self.user_video_graph}")

    def _build_user_tag_matrix(self):
        tag_set = set()
        for v in self.videos_map.values():
            tag_set.add(v['tag'])

        active_users = sorted(self.ops_by_user.keys())
        all_tags = sorted(tag_set)

        self._user_tag_users = active_users
        self._user_tag_tags = all_tags
        self._user_to_idx = {uid: i for i, uid in enumerate(active_users)}
        self._tag_to_idx = {tag: i for i, tag in enumerate(all_tags)}

        dok = {}
        for uid in active_users:
            ops = self.ops_by_user.get(uid) or []
            r = self._user_to_idx[uid]
            for op in ops:
                v = self.videos_map.get(op['video_id'])
                if v is None:
                    continue
                tag = v['tag']
                c = self._tag_to_idx.get(tag)
                if c is None:
                    continue
                score = 1 + (2 if op['liked'] == 1 else 0)
                dok[(r, c)] = dok.get((r, c), 0) + score

        n_users = len(active_users)
        n_tags = max(len(all_tags), 1)

        self.user_tag_matrix = CSRSparseMatrix.from_dok(dok, n_users, n_tags)
        self.user_tag_matrix.normalize_rows_l2()
        print(f"  [CSR] user_tag_matrix: {self.user_tag_matrix}")

    def _build_tag_trie(self):
        self.tag_trie = Trie()
        tag_videos = {}
        for v in self.videos_map.values():
            tag = v['tag']
            if tag not in tag_videos:
                tag_videos[tag] = []
            tag_videos[tag].append(v['id'])
        for tag, vids in tag_videos.items():
            self.tag_trie.insert(tag, vids)
        print(f"  [Trie] tags: {len(self.tag_trie)} 个")

    def _build_daily_views_tree(self):
        daily_views = [0] * 30
        for op in self.operations_list:
            day = op['day']
            if 1 <= day <= 30:
                daily_views[day - 1] += 1
        self.daily_views_tree = SegmentTree(daily_views)
        print(f"  [SegmentTree] daily_views: n=30, total={self.daily_views_tree.total_sum()}")

    def _print_stats(self):
        print(f"\n{'='*50}")
        print(f"  数据结构统计")
        print(f"{'='*50}")
        print(f"  HashMap × 5: users({len(self.users_map)}), videos({len(self.videos_map)}), "
              f"ops_by_user({len(self.ops_by_user)}), ops_by_video({len(self.ops_by_video)})")
        print(f"  Graph × 1:   {self.user_video_graph}")
        print(f"  CSRSparseMatrix × 1: {self.user_tag_matrix}")
        print(f"  Trie × 1:    {self.tag_trie}")
        print(f"  SegmentTree × 1: {self.daily_views_tree}")
        print(f"  LRUCache × 2: similar_users({self.similar_users_cache}), recommend({self.recommend_cache})")
        print(f"{'='*50}\n")

    # ================================================================
    # 公共 API
    # ================================================================

    def get_user(self, uid):
        self._ensure_init()
        return self.users_map.get(int(uid))

    def get_video(self, vid):
        self._ensure_init()
        return self.videos_map.get(int(vid))

    def user_exists(self, uid):
        self._ensure_init()
        return self.users_map.get(int(uid)) is not None

    def video_exists(self, vid):
        self._ensure_init()
        return self.videos_map.get(int(vid)) is not None

    def get_user_operations(self, uid):
        self._ensure_init()
        return self.ops_by_user.get(int(uid)) or []

    def get_video_operations(self, vid):
        self._ensure_init()
        return self.ops_by_video.get(int(vid)) or []

    def get_user_viewed_videos(self, uid):
        self._ensure_init()
        ops = self.get_user_operations(uid)
        return set(op['video_id'] for op in ops)

    def get_similar_users_bfs(self, uid, max_depth=3):
        self._ensure_init()
        start = f"U{uid}"
        if start not in self.user_video_graph.adj:
            return {}
        visited, distances = self.user_video_graph.bfs(start, max_depth=max_depth)
        similar = {}
        for node, dist in distances.items():
            if node.startswith('U') and node != start and dist == 2:
                other_uid = int(node[1:])
                u_videos = self.get_user_viewed_videos(uid)
                o_videos = self.get_user_viewed_videos(other_uid)
                common = len(u_videos & o_videos)
                total = len(u_videos | o_videos)
                sim = common / total if total > 0 else 0
                if sim > 0:
                    similar[other_uid] = sim
        return similar

    def find_similar_users_by_matrix(self, uid, top_k=5):
        self._ensure_init()
        if uid not in self._user_to_idx:
            return []
        idx = self._user_to_idx[uid]
        target_vec = self.user_tag_matrix.get_dense_row(idx)
        sims = self.user_tag_matrix.matvec(target_vec)

        heap = MaxHeap()
        for i, sim in enumerate(sims):
            if i != idx and sim > 0:
                heap.push(sim, self._user_tag_users[i])

        results = []
        for sim, other_uid in heap.top_k(top_k):
            results.append({
                "user_ID": int(other_uid),
                "similarity": round(float(sim), 4)
            })
        return results

    def get_daily_views_range(self, l, r):
        self._ensure_init()
        return self.daily_views_tree.query(l, r)

    def get_daily_views_prefix(self, day):
        self._ensure_init()
        return self.daily_views_tree.prefix_sum(day)

    def search_tags_by_prefix(self, prefix):
        self._ensure_init()
        return self.tag_trie.starts_with(prefix)

    def get_all_user_ids(self):
        self._ensure_init()
        return list(self.ops_by_user.keys())

    def get_all_video_ids(self):
        self._ensure_init()
        return list(self.videos_map.keys())

    def get_users_with_cluster(self, cluster_col='cluster'):
        self._ensure_init()
        path = self._csv_path('users_clustered')
        if not os.path.exists(path):
            path = self._csv_path('users')
        results = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append({
                    'id': int(row.get('id', 0)),
                    'age': row.get('age', ''),
                    'cluster': int(float(row.get(cluster_col, -1))),
                })
        return results

    def get_videos_with_cluster(self):
        self._ensure_init()
        path = self._csv_path('videos_clustered')
        if not os.path.exists(path):
            path = self._csv_path('videos')
        results = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append({
                    'id': int(row.get('id', 0)),
                    'tag': row.get('tag', ''),
                    'views': int(float(row.get('views', 0))),
                    'likes': int(float(row.get('likes', 0))),
                    'cluster': int(float(row.get('cluster', -1))),
                })
        return results

    def explain_recommendation(self, target_uid, recommended_vid):
        """
        Graph BFS 路径回溯: 解释为什么给目标用户推荐该视频。
        在二分图中找最短路径: U_target → V_shared → U_similar → V_recommended
        返回: {"shared_video": vid, "shared_tag": str, "similar_user": uid}
        """
        self._ensure_init()
        start = f"U{target_uid}"
        target = f"V{recommended_vid}"

        if start not in self.user_video_graph.adj:
            return None
        if target not in self.user_video_graph.adj:
            return None

        # BFS 带父节点, 限制深度 3
        parent, distances = self.user_video_graph.bfs_with_parent(start, max_depth=3)

        if target not in parent:
            return None

        # 回溯路径: V_rec ← U_sim ← V_shared ← U_target
        path = self.user_video_graph.reconstruct_path(parent, target)
        if path is None or len(path) < 4:
            return None

        # path[0] = U_target, path[1] = V_shared, path[2] = U_similar, path[3] = V_recommended
        shared_video = int(path[1][1:])
        similar_user = int(path[2][1:])

        v = self.videos_map.get(shared_video)
        shared_tag = v['tag'] if v else '未知'

        return {
            "shared_video": shared_video,
            "shared_tag": shared_tag,
            "similar_user": similar_user
        }

    def get_user_cluster_map(self):
        users = self.get_users_with_cluster()
        return {u['id']: u['cluster'] for u in users}

    def get_video_cluster_map(self):
        videos = self.get_videos_with_cluster()
        return {v['id']: v['cluster'] for v in videos}
