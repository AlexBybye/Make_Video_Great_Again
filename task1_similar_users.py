# -*- coding: utf-8 -*-
import time
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from data_cache import DataCache
import logging
from scipy.sparse import csr_matrix
from functools import lru_cache

# 全局变量用于存储预计算的矩阵
_user_tag_matrix = None
_user_to_idx = None
_unique_users = None

def initialize_matrix():
    """初始化并预计算用户-标签矩阵"""
    global _user_tag_matrix, _user_to_idx, _unique_users
    
    if _user_tag_matrix is None:
        videos_df = DataCache.load_videos()
        operations_df = DataCache.load_operations()
        
        # 预处理数据：计算用户对每个标签的兴趣分数
        operations_with_tag = pd.merge(
            operations_df[['user_id', 'video_id', 'liked']],
            videos_df[['id', 'tag']],
            left_on='video_id',
            right_on='id',
            how='left'
        )
        
        # 计算用户-标签交互分数
        user_tag_scores = operations_with_tag.groupby(['user_id', 'tag']).agg({
            'video_id': 'count',  # 观看次数
            'liked': 'sum'        # 点赞数
        }).reset_index()
        
        # 计算综合分数：观看次数 + 点赞数的加权和
        user_tag_scores['score'] = user_tag_scores['video_id'] + 2 * user_tag_scores['liked']

        # 创建映射字典
        _unique_users = user_tag_scores['user_id'].unique()
        unique_tags = user_tag_scores['tag'].unique()
        _user_to_idx = {uid: idx for idx, uid in enumerate(_unique_users)}
        tag_to_idx = {tag: idx for idx, tag in enumerate(unique_tags)}

        # 构建稀疏矩阵
        rows = np.array([_user_to_idx[user] for user in user_tag_scores['user_id']])
        cols = np.array([tag_to_idx[tag] for tag in user_tag_scores['tag']])
        data = user_tag_scores['score'].values

        # 创建并标准化矩阵
        _user_tag_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(len(_unique_users), len(unique_tags))
        ).tocsr()  # 确保是CSR格式
        
        # L2标准化
        row_norms = np.sqrt(np.array(_user_tag_matrix.power(2).sum(axis=1)).flatten())
        row_norms[row_norms == 0] = 1  # 避免除零
        _user_tag_matrix = _user_tag_matrix.multiply(1 / row_norms[:, np.newaxis]).tocsr()

def find_similar_users(target_user_id):
    """任务1：寻找相似用户群"""

    try:
        t1 = time.time()
        # 验证用户ID是否存在
        operations_df = DataCache.load_operations()
        if target_user_id not in operations_df['user_id'].unique():
            raise ValueError(f"用户ID {target_user_id} 不存在")
            
        logging.info(f"开始处理用户 {target_user_id} 的相似用户分析")

        # 确保矩阵已初始化
        initialize_matrix()
        
        # 获取目标用户的向量
        target_idx = _user_to_idx[target_user_id]
        target_vector = _user_tag_matrix[target_idx].tocsr()
        
        # 计算相似度（使用矩阵乘法）
        similarities = _user_tag_matrix.dot(target_vector.T).toarray().flatten()
        
        # 使用 argpartition 快速找出前k个最大值
        k = 6  # 需要5个最相似的用户，多取一个以排除自己
        top_indices = np.argpartition(similarities, -k)[-k:]
        top_indices = top_indices[np.argsort(similarities[top_indices])][::-1]
        
        # 排除目标用户自己
        top_indices = top_indices[top_indices != target_idx][:5]
        
        # 构建结果
        result = [
            {"user_ID": int(_unique_users[idx]), 
             "similarity": round(float(similarities[idx]), 4)}
            for idx in top_indices
        ]
        
        logging.info(f"成功找到用户 {target_user_id} 的相似用户")
        t2 = time.time()
        print(f"task1模拟耗时: {t2 - t1:.4f} 秒")
        return result

    except Exception as e:
        logging.error(f"寻找相似用户失败: {str(e)}")
        raise

