# ds/sparse_matrix.py — 自建 CSR 稀疏矩阵
# 不依赖 scipy, 从零实现 Compressed Sparse Row 格式
# 支持: 矩阵乘法 (点积), L2 行归一化, Top-K 相似度提取

import math


class CSRSparseMatrix:
    """
    Compressed Sparse Row (CSR) 格式的稀疏矩阵。
    用于用户-标签矩阵和用户-视频交互矩阵的高效存储和相似度计算。

    CSR 三元组:
      - data:   非零元素值
      - indices: 每个非零元素的列索引
      - indptr:  每行在 data/indices 中的起始位置 (长度 = n_rows + 1)
    """

    def __init__(self, data, indices, indptr, n_rows, n_cols):
        self.data = list(data)
        self.indices = list(indices)
        self.indptr = list(indptr)
        self.n_rows = n_rows
        self.n_cols = n_cols

    @classmethod
    def from_dok(cls, dok_dict, n_rows, n_cols):
        """
        从 Dictionary of Keys 构建 CSR 矩阵。
        dok_dict: {(row, col): value, ...}
        """
        rows_data = [[] for _ in range(n_rows)]
        rows_cols = [[] for _ in range(n_rows)]

        for (r, c), val in dok_dict.items():
            if val != 0:
                rows_data[r].append(float(val))
                rows_cols[r].append(int(c))

        data = []
        indices = []
        indptr = [0]

        for r in range(n_rows):
            pairs = sorted(zip(rows_cols[r], rows_data[r]))
            for col, val in pairs:
                indices.append(col)
                data.append(val)
            indptr.append(len(data))

        return cls(data, indices, indptr, n_rows, n_cols)

    @classmethod
    def from_row_lists(cls, row_elements, n_cols):
        """
        从每行元素列表构建 CSR。
        row_elements: [(col, value), ...] 的列表, 按行索引排列
        """
        n_rows = len(row_elements)
        data = []
        indices = []
        indptr = [0]

        for row_idx, elements in enumerate(row_elements):
            for col, val in sorted(elements, key=lambda x: x[0]):
                indices.append(col)
                data.append(float(val))
            indptr.append(len(data))

        return cls(data, indices, indptr, n_rows, n_cols)

    def get_row(self, i):
        """返回第 i 行的 (col_indices, values)"""
        start = self.indptr[i]
        end = self.indptr[i + 1]
        return self.indices[start:end], self.data[start:end]

    def row_dot(self, i, j):
        """
        计算第 i 行和第 j 行的点积 (用于余弦相似度分子)。
        使用双指针合并两个有序索引序列, O(nnz_i + nnz_j)。
        """
        cols_a, vals_a = self.get_row(i)
        cols_b, vals_b = self.get_row(j)

        result = 0.0
        pa, pb = 0, 0
        while pa < len(cols_a) and pb < len(cols_b):
            if cols_a[pa] < cols_b[pb]:
                pa += 1
            elif cols_a[pa] > cols_b[pb]:
                pb += 1
            else:
                result += vals_a[pa] * vals_b[pb]
                pa += 1
                pb += 1
        return result

    def row_norm(self, i):
        """计算第 i 行的 L2 范数"""
        _, vals = self.get_row(i)
        return math.sqrt(sum(v * v for v in vals))

    def cosine_similarity(self, i, j):
        """计算第 i 行和第 j 行的余弦相似度"""
        dot = self.row_dot(i, j)
        if dot == 0:
            return 0.0
        norm_i = self.row_norm(i)
        norm_j = self.row_norm(j)
        if norm_i == 0 or norm_j == 0:
            return 0.0
        return dot / (norm_i * norm_j)

    def normalize_rows_l2(self):
        """
        L2 行归一化 (in-place), 使每行向量长度为 1。
        用于余弦相似度等价于内积。
        """
        for i in range(self.n_rows):
            norm = self.row_norm(i)
            if norm > 0:
                start = self.indptr[i]
                end = self.indptr[i + 1]
                for k in range(start, end):
                    self.data[k] /= norm

    def dot_vector(self, i, vec):
        """
        计算第 i 行与稠密向量 vec 的内积。
        用于获取目标用户向量与所有用户的相似度。
        vec: 列表或数组, 长度为 n_cols
        """
        cols, vals = self.get_row(i)
        result = 0.0
        for col, val in zip(cols, vals):
            result += val * vec[col]
        return result

    def matvec(self, vec):
        """
        矩阵-向量乘法: 返回 self @ vec, 结果长度为 n_rows。
        用于一次计算所有行与目标向量的相似度。
        """
        result = [0.0] * self.n_rows
        for i in range(self.n_rows):
            result[i] = self.dot_vector(i, vec)
        return result

    def get_dense_row(self, i):
        """将第 i 行展开为稠密列表 (仅用于小规模调试)"""
        dense = [0.0] * self.n_cols
        cols, vals = self.get_row(i)
        for c, v in zip(cols, vals):
            dense[c] = v
        return dense

    def shape(self):
        return (self.n_rows, self.n_cols)

    def nnz(self):
        return len(self.data)

    def __repr__(self):
        return f"CSRSparseMatrix({self.n_rows}x{self.n_cols}, nnz={self.nnz()})"
