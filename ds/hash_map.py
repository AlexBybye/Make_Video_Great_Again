# ds/hash_map.py — 自定义 HashMap (开放寻址 + 线性探测)
# 用于 O(1) 用户/视频/操作按 ID 查询

class HashMap:
    """
    开放寻址哈希表, 使用线性探测解决冲突。
    负载因子超过 0.7 时自动扩容。
    支持任意可哈希 key, 存储 key-value 对。
    """

    _EMPTY = object()   # 标记空槽
    _DELETED = object() # 标记已删除槽 (墓碑)

def __init__(self, initial_capacity=1024):
        self._capacity = max(8, int(initial_capacity or 0))
        self._size = 0
        self._keys = [self._EMPTY] * self._capacity
        self._vals = [None] * self._capacity
        self._deleted_count = 0

    def __len__(self):
        return self._size

    def __contains__(self, key):
        return self.get(key, self._EMPTY) is not self._EMPTY

    def _hash(self, key):
        return hash(key) % self._capacity

    def _probe(self, key):
        """线性探测: 找到 key 对应的槽位索引"""
        idx = self._hash(key)
        first_deleted = -1
        while self._keys[idx] is not self._EMPTY:
            if self._keys[idx] is self._DELETED:
                if first_deleted == -1:
                    first_deleted = idx
            elif self._keys[idx] == key:
                return idx
            idx = (idx + 1) % self._capacity
        return first_deleted if first_deleted != -1 else idx

    def put(self, key, value):
        """插入/更新键值对"""
        if (self._size + self._deleted_count) * 2 > self._capacity:
            self._resize(self._capacity * 2)

        idx = self._probe(key)
        if self._keys[idx] is self._EMPTY or self._keys[idx] is self._DELETED:
            self._keys[idx] = key
            self._vals[idx] = value
            self._size += 1
            if self._keys[idx] is self._DELETED:
                self._deleted_count -= 1
        else:
            self._vals[idx] = value

    def get(self, key, default=None):
        """获取 key 对应的 value"""
        idx = self._hash(key)
        while self._keys[idx] is not self._EMPTY:
            if self._keys[idx] is not self._DELETED and self._keys[idx] == key:
                return self._vals[idx]
            idx = (idx + 1) % self._capacity
        return default

    def remove(self, key):
        """删除键值对 (懒惰删除, 留墓碑)"""
        idx = self._hash(key)
        while self._keys[idx] is not self._EMPTY:
            if self._keys[idx] is not self._DELETED and self._keys[idx] == key:
                self._keys[idx] = self._DELETED
                self._vals[idx] = None
                self._size -= 1
                self._deleted_count += 1
                return True
            idx = (idx + 1) % self._capacity
        return False

    def keys(self):
        """返回所有 key 的列表"""
        result = []
        for i in range(self._capacity):
            k = self._keys[i]
            if k is not self._EMPTY and k is not self._DELETED:
                result.append(k)
        return result

    def values(self):
        """返回所有 value 的列表"""
        result = []
        for i in range(self._capacity):
            k = self._keys[i]
            if k is not self._EMPTY and k is not self._DELETED:
                result.append(self._vals[i])
        return result

    def items(self):
        """返回所有 (key, value) 对的列表"""
        result = []
        for i in range(self._capacity):
            k = self._keys[i]
            if k is not self._EMPTY and k is not self._DELETED:
                result.append((k, self._vals[i]))
        return result

    def _resize(self, new_capacity):
        """扩容并重新哈希所有元素"""
        old_keys = self._keys
        old_vals = self._vals
        old_capacity = self._capacity

        self._capacity = new_capacity
        self._keys = [self._EMPTY] * new_capacity
        self._vals = [None] * new_capacity
        self._size = 0
        self._deleted_count = 0

        for i in range(old_capacity):
            k = old_keys[i]
            if k is not self._EMPTY and k is not self._DELETED:
                self.put(k, old_vals[i])

    def __repr__(self):
        items = [(k, self._vals[i]) for i, k in enumerate(self._keys)
                 if k is not self._EMPTY and k is not self._DELETED]
        return f"HashMap({items[:10]}{'...' if len(items) > 10 else ''})"
