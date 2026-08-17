# ds/max_heap.py — 自建二叉最大堆
# 用于 Top-K 相似用户/推荐视频提取, 避免全排序 O(n log n)
# 堆顶为最大元素, push/pop 均为 O(log n)

class MaxHeap:
    """
    二叉最大堆。
    每个元素为 (key, value) 元组, key 用于比较 (通常是分数/相似度)。
    支持 Top-K 提取: 取堆顶 K 次即可, O(k log n)。
    """

    def __init__(self, items=None):
        """
        items: 可选的初始元素列表 [(key, value), ...]
        """
        self._heap = []
        if items:
            self._heap = list(items)
            self._build_heap()

    def _parent(self, i):
        return (i - 1) // 2

    def _left(self, i):
        return 2 * i + 1

    def _right(self, i):
        return 2 * i + 2

    def _swap(self, i, j):
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _sift_up(self, i):
        """上浮: 将索引 i 的元素向上调整"""
        while i > 0:
            p = self._parent(i)
            if self._heap[i][0] > self._heap[p][0]:
                self._swap(i, p)
                i = p
            else:
                break

    def _sift_down(self, i):
        """下沉: 将索引 i 的元素向下调整"""
        n = len(self._heap)
        while True:
            largest = i
            l = self._left(i)
            r = self._right(i)

            if l < n and self._heap[l][0] > self._heap[largest][0]:
                largest = l
            if r < n and self._heap[r][0] > self._heap[largest][0]:
                largest = r

            if largest != i:
                self._swap(i, largest)
                i = largest
            else:
                break

    def _build_heap(self):
        """Floyd 建堆法: O(n) 时间复杂度"""
        n = len(self._heap)
        for i in range(n // 2 - 1, -1, -1):
            self._sift_down(i)

    def push(self, key, value):
        """插入元素, O(log n)"""
        self._heap.append((key, value))
        self._sift_up(len(self._heap) - 1)

    def pop(self):
        """弹出最大元素, O(log n)"""
        if not self._heap:
            return None
        if len(self._heap) == 1:
            return self._heap.pop()
        result = self._heap[0]
        self._heap[0] = self._heap.pop()
        self._sift_down(0)
        return result

    def peek(self):
        """查看堆顶 (最大元素), O(1)"""
        if self._heap:
            return self._heap[0]
        return None

    def top_k(self, k):
        """提取 Top-K 个最大元素 (按 key 降序), O(k log n)"""
        results = []
        # 复制当前堆进行临时操作
        temp = MaxHeap(self._heap[:])
        for _ in range(min(k, len(temp._heap))):
            item = temp.pop()
            if item:
                results.append(item)
        return results

    def pop_all_sorted(self):
        """弹出所有元素, key 降序排列, O(n log n)"""
        results = []
        while self._heap:
            results.append(self.pop())
        return results

    def __len__(self):
        return len(self._heap)

    def __bool__(self):
        return len(self._heap) > 0

    def __repr__(self):
        return f"MaxHeap(size={len(self._heap)}, top={self.peek()})"
