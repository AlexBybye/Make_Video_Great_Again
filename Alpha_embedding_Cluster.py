# -*- coding: utf-8 -*-
import time
import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
import os
import logging

logging.basicConfig(filename='results/embedding.log', level=logging.INFO)


def get_cluster_embeddings(embedding_dim=128):
    """
    使用 SVD 实现 '聚类 -> 向量' (Cluster-to-Vector) 特征增强
    """
    try:
        t1 = time.time()

        # 1. 加载数据
        users_clustered_df = pd.read_csv('data/users_clustered.csv')
        videos_clustered_df = pd.read_csv('data/videos_clustered.csv')
        operations_df = pd.read_csv('data/operations.csv')

        # 简化：给 videos_clustered_df 的 'cluster' 列重命名为 'video_cluster'
        videos_clustered_df = videos_clustered_df[['id', 'cluster']].rename(
            columns={'id': 'video_id', 'cluster': 'video_cluster'})

        # 简化：给 users_clustered_df 的 'cluster' 列重命名为 'user_cluster'
        users_clustered_df = users_clustered_df[['id', 'cluster']].rename(
            columns={'id': 'user_id', 'cluster': 'user_cluster'})

        # 2. 合并数据，关联操作和簇 ID
        interaction_df = operations_df.merge(
            users_clustered_df, on='user_id', how='left'
        ).merge(
            videos_clustered_df, on='video_id', how='left'
        )

        # 剔除未分配簇（cluster=-1 或 NaN）的记录
        interaction_df = interaction_df.dropna(subset=['user_cluster', 'video_cluster'])
        interaction_df['user_cluster'] = interaction_df['user_cluster'].astype(int)
        interaction_df['video_cluster'] = interaction_df['video_cluster'].astype(int)

        # 3. 构建用户簇-视频簇交互矩阵 R_C

        # 定义交互强度：使用总点赞数和平均观看次数的组合作为评分（这里简化为总点赞数）
        # 实际项目中应使用更复杂的加权，例如平均完播率
        interaction_df['score'] = interaction_df['liked']  # 简化：只用点赞作为正反馈

        cluster_interaction = interaction_df.groupby(['user_cluster', 'video_cluster'])['score'].sum().reset_index(
            name='total_score')

        # 枢轴操作：将 DataFrame 转化为矩阵 R_C (行：用户簇，列：视频簇)
        R_C = cluster_interaction.pivot(
            index='user_cluster',
            columns='video_cluster',
            values='total_score'
        ).fillna(0)  # 缺乏交互的簇对填充为 0

        R_C_matrix = R_C.values

        # 4. SVD 分解

        # 确保降维维度不大于矩阵的最小维度
        n_components = min(embedding_dim, R_C_matrix.shape[0], R_C_matrix.shape[1])
        if n_components < 1:
            raise ValueError("簇矩阵维度过小，无法进行SVD。请检查聚类数量。")

        # 使用 TruncatedSVD，适用于稀疏或非负矩阵
        svd = TruncatedSVD(n_components=n_components, random_state=42)

        # SVD 对 R_C (用户簇 x 视频簇) 进行分解
        # 得到 U * S * V^T

        # 拟合 R_C 矩阵
        svd.fit(R_C_matrix)

        # U 矩阵（用户簇 Embedding）
        U_matrix = svd.transform(R_C_matrix)

        # V^T 矩阵 (视频簇 Embedding)
        V_matrix = svd.components_.T

        # 5. 结果处理和保存

        # 由于 U_matrix 和 V_matrix 的维度可能不同 (U: N_U x k, V: N_V x k)，
        # 我们使用标准方法，将奇异值 S 乘回其中一个矩阵，保证它们的“能量”对等

        S_sqrt = np.diag(np.sqrt(svd.singular_values_))

        # 最终用户簇 Embedding: E_CU = U * S^(1/2)
        E_CU = U_matrix @ S_sqrt
        # 最终视频簇 Embedding: E_CV = V * S^(1/2)
        E_CV = V_matrix @ S_sqrt

        # 转化为 DataFrame 方便后续使用
        user_cluster_ids = R_C.index
        video_cluster_ids = R_C.columns

        # 构造用户簇 Embedding DataFrame
        E_CU_df = pd.DataFrame(E_CU, index=user_cluster_ids, columns=[f'U_Emb_{i}' for i in range(E_CU.shape[1])])
        E_CU_df.index.name = 'user_cluster_id'

        # 构造视频簇 Embedding DataFrame
        E_CV_df = pd.DataFrame(E_CV, index=video_cluster_ids, columns=[f'V_Emb_{i}' for i in range(E_CV.shape[1])])
        E_CV_df.index.name = 'video_cluster_id'

        # 保存结果
        os.makedirs('results', exist_ok=True)
        E_CU_df.to_csv('results/user_cluster_embeddings.csv')
        E_CV_df.to_csv('results/video_cluster_embeddings.csv')

        t2 = time.time()
        print(f"聚类到向量任务耗时: {t2 - t1:.4f} 秒")

        return {
            "user_embeddings_shape": E_CU.shape,
            "video_embeddings_shape": E_CV.shape,
            "message": "用户簇和视频簇 Embedding 已成功生成并保存到 results 文件夹。"
        }

    except Exception as e:
        logging.error(f"聚类到向量失败: {str(e)}", exc_info=True)
        return {"error": f"聚类到向量失败: {str(e)}"}