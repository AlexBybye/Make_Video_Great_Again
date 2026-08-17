# ds/trie.py — 自建 Trie (前缀树)
# 用于标签/视频名称的快速前缀匹配和模糊搜索
# insert/search/prefix_search 均为 O(len(word))

class TrieNode:
    """Trie 节点"""
    __slots__ = ('children', 'is_end', 'value')

    def __init__(self):
        self.children = {}    # char -> TrieNode
        self.is_end = False   # 是否为完整词的结尾
        self.value = None     # 词末尾存储的值 (如视频ID列表)


class Trie:
    """
    前缀树 (Trie)。
    用于标签名/视频名称的快速前缀搜索。
    """

    def __init__(self):
        self.root = TrieNode()
        self._size = 0

    def insert(self, word, value=None):
        """插入一个词, 可附带 value"""
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        if not node.is_end:
            self._size += 1
        node.is_end = True
        node.value = value

    def search(self, word):
        """精确搜索: 返回 value 或 None"""
        node = self.root
        for ch in word:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node.value if node.is_end else None

    def starts_with(self, prefix):
        """
        前缀搜索: 返回所有以 prefix 开头的 (word, value) 列表。
        使用 DFS 收集子树中所有完整词。
        """
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]

        results = []
        self._collect_words(node, list(prefix), results)
        return results

    def _collect_words(self, node, prefix_chars, results):
        """DFS 收集以当前节点为根的子树中所有完整词"""
        if node.is_end:
            results.append((''.join(prefix_chars), node.value))
        for ch in sorted(node.children.keys()):
            prefix_chars.append(ch)
            self._collect_words(node.children[ch], prefix_chars, results)
            prefix_chars.pop()

    def contains_prefix(self, prefix):
        """检查是否存在以 prefix 开头的词"""
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True

    def __len__(self):
        return self._size

    def __contains__(self, word):
        return self.search(word) is not None

    def __repr__(self):
        return f"Trie(words={self._size})"
