# ds/lru_cache.py — 自建 LRU Cache (双向链表 + HashMap)
# 用于热点数据缓存, 淘汰最近最少使用的条目
# get/put 均为 O(1)

class _DLLNode:
    """双向链表节点"""
    __slots__ = ('key', 'value', 'prev', 'next')

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    """
    基于 双向链表 + HashMap 的 LRU 缓存。
    - 双向链表维护访问顺序 (头=最新, 尾=最旧)
    - HashMap (Python dict) 实现 O(1) 查找
    - 超过容量时淘汰尾部节点
    """

    def __init__(self, capacity=1000):
        self.capacity = capacity
        self._cache = {}          # key -> _DLLNode
        # 哨兵头尾节点
        self._head = _DLLNode()
        self._tail = _DLLNode()
        self._head.next = self._tail
        self._tail.prev = self._head

    def _remove_node(self, node):
        """从链表中移除节点"""
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_head(self, node):
        """将节点插入链表头部 (表示最近使用)"""
        node.next = self._head.next
        node.prev = self._head
        self._head.next.prev = node
        self._head.next = node

    def _move_to_head(self, node):
        """将已有节点移至头部"""
        self._remove_node(node)
        self._add_to_head(node)

    def _pop_tail(self):
        """移除并返回尾部节点 (最久未使用)"""
        node = self._tail.prev
        if node is self._head:
            return None
        self._remove_node(node)
        return node

    def get(self, key):
        """获取缓存值, 并将该项标记为最近使用, O(1)"""
        if key in self._cache:
            node = self._cache[key]
            self._move_to_head(node)
            return node.value
        return None

    def put(self, key, value):
        """插入/更新缓存, O(1)"""
        if key in self._cache:
            node = self._cache[key]
            node.value = value
            self._move_to_head(node)
            return

        node = _DLLNode(key, value)
        self._cache[key] = node
        self._add_to_head(node)

        if len(self._cache) > self.capacity:
            evicted = self._pop_tail()
            if evicted:
                del self._cache[evicted.key]

    def remove(self, key):
        """手动删除缓存项, O(1)"""
        if key in self._cache:
            node = self._cache[key]
            self._remove_node(node)
            del self._cache[key]

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._head.next = self._tail
        self._tail.prev = self._head

    def __len__(self):
        return len(self._cache)

    def __contains__(self, key):
        return key in self._cache

    def keys(self):
        return self._cache.keys()

    def __repr__(self):
        return f"LRUCache(size={len(self._cache)}, capacity={self.capacity})"
