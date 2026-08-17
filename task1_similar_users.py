# -*- coding: utf-8 -*-
# task1_similar_users.py — 相似用户分析
# 使用自建 CSRSparseMatrix + MaxHeap 替代 scipy CSR + numpy argpartition
# 数据结构: HashMap (O(1)查询) + CSRSparseMatrix (稀疏存储) + MaxHeap (Top-K)

import time
import logging
from ds.data_store import DataStore


def find_similar_users(target_user_id, top_k=5):
    """使用自建 CSR 稀疏矩阵 + 最大堆查找相似用户"""

    t1 = time.time()
    store = DataStore()

    # HashMap O(1) 验证用户存在
    if not store.user_exists(target_user_id):
        raise ValueError(f"用户ID {target_user_id} 不存在")

    logging.info(f"[Task1] 使用自建 CSR + MaxHeap 查找用户 {target_user_id} 的相似用户")

    # CSRSparseMatrix.matvec + MaxHeap.top_k 提取 Top-K
    results = store.find_similar_users_by_matrix(target_user_id, top_k=top_k)

    t2 = time.time()
    print(f"task1耗时 (自建数据结构): {t2 - t1:.4f} 秒")
    return results
