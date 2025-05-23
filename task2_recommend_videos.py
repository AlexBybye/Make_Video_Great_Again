# -*- coding: utf-8 -*-
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from data_cache import DataCache
import logging
from scipy.sparse import csr_matrix
from task1_similar_users import find_similar_users, initialize_matrix
from functools import lru_cache

@lru_cache(maxsize=1)
def get_video_data():
    """缓存视频数据"""
    return DataCache.load_videos()

def recommend_videos(target_user_id):
    """任务2：推荐相关视频"""
    try:
        t1 = time.time()
        # 使用缓存数据
        videos_df = get_video_data()
        operations_df = DataCache.load_operations()
        
        # 验证用户ID是否存在
        if target_user_id not in operations_df['user_id'].unique():
            raise ValueError(f"用户ID {target_user_id} 不存在")
            
        logging.info(f"开始处理用户 {target_user_id} 的视频推荐")

        # 获取用户已观看的视频（使用集合操作）
        user_viewed_videos = set(operations_df[operations_df['user_id'] == target_user_id]['video_id'])
        logging.info(f"用户已观看视频数: {len(user_viewed_videos)}")

        # 获取相似用户（复用task1的结果和矩阵）
        similar_users_result = find_similar_users(target_user_id)
        similar_users = [item["user_ID"] for item in similar_users_result]
        
        # 获取更多相似用户（使用numpy操作优化）
        all_users = np.array(list(operations_df['user_id'].unique()))
        mask = ~np.isin(all_users, similar_users)
        additional_users = all_users[mask][:45]
        similar_users.extend(additional_users)

        # 使用向量化操作获取候选视频
        similar_users_ops = operations_df[operations_df['user_id'].isin(similar_users)]
        candidate_videos = set(similar_users_ops['video_id']) - user_viewed_videos

        if len(candidate_videos) == 0:
            raise ValueError("没有找到合适的推荐视频")

        # 预处理视频数据
        video_data = []
        video_ids = list(candidate_videos)
        
        # 使用 DataFrame 操作代替循环
        video_ops_df = similar_users_ops[similar_users_ops['video_id'].isin(candidate_videos)]
        video_stats = video_ops_df.groupby('video_id').agg({
            'user_id': ['count', lambda x: set(x)],
            'liked': 'mean'
        }).reset_index()
        
        # 计算特征（向量化操作）
        top_similar_users = set(similar_users[:5])
        video_stats['user_overlap'] = video_stats[('user_id', '<lambda_0>')].apply(
            lambda x: len(x & top_similar_users) / 5
        )
        
        # 构建特征矩阵
        features = np.array([
            video_stats[('user_id', 'count')].values,  # 观看次数
            video_stats['liked']['mean'].values,       # 点赞率
            video_stats['user_overlap'].values         # 用户重叠度
        ]).T
        
        # 标准化特征
        features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)
        
        # 计算综合得分
        base_scores = video_stats[('user_id', 'count')].values * \
                     (1 + video_stats['liked']['mean'].values) * \
                     (1 + video_stats['user_overlap'].values)
        final_scores = base_scores * (1 + features[:, 2])  # 增加用户重叠度权重
        
        # 获取前10个推荐
        top_indices = np.argpartition(final_scores, -10)[-10:]
        top_indices = top_indices[np.argsort(final_scores[top_indices])][::-1]
        
        # 构建结果
        result = []
        for idx in top_indices:
            video_id = video_stats['video_id'].iloc[idx]
            video_tag = videos_df[videos_df['id'] == video_id]['tag'].iloc[0]
            result.append({
                "Video_ID": int(video_id),
                "label": video_tag,
                "Overall_rating": round(float(final_scores[idx]), 2)
            })

        logging.info(f"成功为用户 {target_user_id} 生成 {len(result)} 个视频推荐")
        t2 = time.time()
        print(f"task2模拟耗时: {t2 - t1:.4f} 秒")
        return result

    except Exception as e:
        logging.error(f"生成视频推荐失败: {str(e)}")
        raise