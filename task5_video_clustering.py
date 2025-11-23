# -*- coding: utf-8 -*-
import time
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
import matplotlib.pyplot as plt
import os
import logging
from sklearn.preprocessing import normalize

# from PyQt6.QtGui import QPixmap # 在非GUI环境下不需要导入

# 配置日志
logging.basicConfig(filename='results/clustering.log', level=logging.INFO)


def plot_clusters(labels, reduced_data, n_clusters):
    """绘制聚类结果图"""
    plt.figure(figsize=(10, 8))
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 绘制散点图
    scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1],
                          c=labels, cmap='viridis',
                          alpha=0.7, s=20, edgecolor='k', linewidth=0.3)

    # 标记聚类中心（只对用于聚类的 reduced_data 计算中心）
    # centers = np.array([reduced_data[labels == i].mean(axis=0) for i in range(n_clusters)])
    # plt.scatter(centers[:, 0], centers[:, 1],
    #             c='red', s=200, alpha=0.9, marker='X', edgecolor='k')

    # 添加标签和标题
    plt.title(f'视频聚类结果 (k={n_clusters})')
    plt.xlabel('SVD 主成分 1')
    plt.ylabel('SVD 主成分 2')
    plt.colorbar(scatter, label='聚类')
    plt.grid(True, alpha=0.2)

    # 保存图像
    plot_path = 'results/video_clusters.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    return plot_path


def cluster_videos(n_clusters=5, sample_size=5000):
    """视频聚类分析"""
    try:
        t1 = time.time()
        os.makedirs('results', exist_ok=True)
        os.makedirs('data', exist_ok=True)

        # 1. 数据加载
        videos_df = pd.read_csv('data/videos.csv')
        operations_df = pd.read_csv('data/operations.csv')

        # 2. 构建交互矩阵
        # (保持原有的用户-视频交互矩阵构建和加权逻辑不变)
        video_ids_in_op = operations_df['video_id'].unique()
        user_ids = operations_df['user_id'].unique()

        video_to_idx = {video: idx for idx, video in enumerate(video_ids_in_op)}
        user_to_idx = {user: idx for idx, user in enumerate(user_ids)}

        # 行为权重分配
        operations_df['weight'] = 1.0
        operations_df.loc[operations_df['liked'] == 1, 'weight'] = 2.0

        rows = operations_df['user_id'].map(user_to_idx)
        cols = operations_df['video_id'].map(video_to_idx)
        data = operations_df['weight'].values

        sparse_matrix = csr_matrix((data, (rows, cols)),
                                   shape=(len(user_ids), len(video_ids_in_op)))

        # 3. 只取有交互的视频
        video_user_matrix = sparse_matrix.T
        nonzero_indices = np.array(video_user_matrix.getnnz(axis=1) > 0).flatten()
        video_user_matrix = video_user_matrix[nonzero_indices]
        video_ids_clustered = video_ids_in_op[nonzero_indices]  # 真正用于聚类的视频ID

        # 4. 采样部分视频加速 (仅在视频量大时使用)
        video_matrix_for_cluster = video_user_matrix
        video_ids_for_cluster = video_ids_clustered

        if sample_size and video_user_matrix.shape[0] > sample_size:
            idx = np.random.choice(video_user_matrix.shape[0], sample_size, replace=False)
            video_matrix_for_cluster = video_user_matrix[idx]
            video_ids_for_cluster = video_ids_clustered[idx]

        # 5. 归一化处理
        video_matrix_for_cluster = normalize(video_matrix_for_cluster, norm='l2', axis=1)

        # 6. 降维
        # 注意：这里 n_components=2 只是为了可视化，实际 embedding 维度应该更高，
        # 但我们为了保持原代码逻辑，先用 2 维聚类
        n_components_svd = min(2, video_matrix_for_cluster.shape[1] - 1)
        svd = TruncatedSVD(n_components=n_components_svd, random_state=42)
        video_user_matrix_reduced = svd.fit_transform(video_matrix_for_cluster)

        # 7. 聚类
        kmeans = MiniBatchKMeans(n_clusters=n_clusters,
                                 random_state=42,
                                 batch_size=500,
                                 n_init=3)
        video_labels = kmeans.fit_predict(video_user_matrix_reduced)

        # 8. 结果处理：将聚类标签映射回原始 videos_df
        cluster_mapping = pd.DataFrame({
            'id': video_ids_for_cluster,
            'cluster': video_labels
        })

        # 将聚类结果合并到原始 videos_df
        result_df = videos_df.merge(cluster_mapping, on='id', how='left')

        # --- 💥 修正点 💥 ---
        # 对于没有交互数据而没有聚类标签的视频（它们是 NaN），
        # 填充为最后一个有效簇的 ID (n_clusters - 1)。
        # 确保填充值在 [0, n_clusters-1] 范围内。
        fill_cluster_id = n_clusters - 1 if n_clusters > 0 else 0

        result_df['cluster'] = result_df['cluster'].fillna(fill_cluster_id).astype(int)
        # 9. 保存结果和可视化
        output_path = 'data/videos_clustered.csv'
        result_df.to_csv(output_path, index=False)
        logging.info(f"视频聚类结果已保存至: {output_path}")

        plot_path = plot_clusters(video_labels, video_user_matrix_reduced, n_clusters)

        t2 = time.time()
        print(f"task5模拟耗时: {t2 - t1:.4f} 秒")

        return {
            "data": result_df[['id', 'tag', 'views', 'likes', 'cluster']].head(10).to_dict('records'),
            "plot_path": plot_path
        }

    except Exception as e:
        logging.error(f"聚类失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"视频聚类失败: {str(e)}")