# ds/segment_tree.py — 自建线段树
# 用于区间和查询 (O(log n)), 替代 pandas groupby 的 O(n) 扫描
# Task 3 热度预测中: 快速查询任一时间区间的累计观看量

class SegmentTree:
    """
    线段树 (Segment Tree), 支持区间求和查询和单点更新。
    用于视频观看量的快速区间聚合。

    内部使用数组存储: tree[i] 覆盖某段区间的和。
    - build: O(n)
    - query(l, r): 查询 [l, r] 区间和, O(log n)
    - update(idx, val): 单点更新, O(log n)
    """

    def __init__(self, arr):
        """
        arr: 初始数组 (list)
        """
        self._n = len(arr)
        self._arr = list(arr)
        # 线段树数组, 大小 4n 保证足够
        self._tree = [0] * (4 * self._n)
        if self._n > 0:
            self._build(1, 0, self._n - 1)

    def _build(self, node, left, right):
        """递归建树"""
        if left == right:
            self._tree[node] = self._arr[left]
            return
        mid = (left + right) // 2
        self._build(node * 2, left, mid)
        self._build(node * 2 + 1, mid + 1, right)
        self._tree[node] = self._tree[node * 2] + self._tree[node * 2 + 1]

    def update(self, idx, value):
        """单点更新: 将 arr[idx] 设为 value"""
        diff = value - self._arr[idx]
        self._arr[idx] = value
        self._update_tree(1, 0, self._n - 1, idx, diff)

    def _update_tree(self, node, left, right, idx, diff):
        if left == right:
            self._tree[node] += diff
            return
        mid = (left + right) // 2
        if idx <= mid:
            self._update_tree(node * 2, left, mid, idx, diff)
        else:
            self._update_tree(node * 2 + 1, mid + 1, right, idx, diff)
        self._tree[node] = self._tree[node * 2] + self._tree[node * 2 + 1]

    def query(self, l, r):
        """查询区间 [l, r] 的和 (闭区间)"""
        if l < 0:
            l = 0
        if r >= self._n:
            r = self._n - 1
        if l > r:
            return 0
        return self._query_tree(1, 0, self._n - 1, l, r)

    def _query_tree(self, node, left, right, ql, qr):
        """递归区间查询"""
        if ql <= left and right <= qr:
            return self._tree[node]
        if right < ql or left > qr:
            return 0
        mid = (left + right) // 2
        return (self._query_tree(node * 2, left, mid, ql, qr) +
                self._query_tree(node * 2 + 1, mid + 1, right, ql, qr))

    def prefix_sum(self, idx):
        """前缀和: arr[0] + ... + arr[idx], O(log n)"""
        if idx < 0:
            return 0
        return self.query(0, idx)

    def total_sum(self):
        """总和, O(1)"""
        return self._tree[1] if self._n > 0 else 0

    def __len__(self):
        return self._n

    def __getitem__(self, idx):
        return self._arr[idx]

    def __repr__(self):
        return f"SegmentTree(n={self._n}, total={self.total_sum()})"
