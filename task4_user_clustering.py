# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import IncrementalPCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import os
import logging
from PyQt6.QtGui import QPixmap

# 配置日志
logging.basicConfig(filename='results/user_clustering.log', level=logging.INFO)


def plot_user_clusters(labels, reduced_data, n_clusters):
    """绘制用户聚类结果图"""
    plt.figure(figsize=(10, 8))
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1],
                          c=labels, cmap='viridis',
                          alpha=0.7, s=20, edgecolor='k', linewidth=0.3)

    plt.title(f'用户聚类结果 (k={n_clusters})')
    plt.xlabel('PCA 主成分 1')
    plt.ylabel('PCA 主成分 2')
    plt.colorbar(scatter, label='聚类')
    plt.grid(True, alpha=0.2)

    plot_path = 'results/user_clusters.png'
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    return plot_path


def cluster_users(n_clusters=10):
    """
    基于观看兴趣相似性对用户进行聚类
    返回包含聚类结果的字典
    """
    try:
        # 加载数据
        users_df = pd.read_csv('data/users.csv')
        videos_df = pd.read_csv('data/videos.csv')
        operations_df = pd.read_csv('data/operations.csv')

        # 创建用户-标签矩阵
        operations_with_tag = operations_df.merge(
            videos_df[['id', 'tag']],
            left_on='video_id',
            right_on='id',
            how='left'
        )

        # 构建稀疏矩阵
        tags = operations_with_tag['tag'].unique()
        user_tag_counts = operations_with_tag.groupby(['user_id', 'tag']).size().reset_index(name='count')

        user_to_idx = {user_id: idx for idx, user_id in enumerate(user_tag_counts['user_id'].unique())}
        tag_to_idx = {tag: idx for idx, tag in enumerate(tags)}

        rows = user_tag_counts['user_id'].map(user_to_idx)
        cols = user_tag_counts['tag'].map(tag_to_idx)
        data = user_tag_counts['count']

        user_tag_sparse = csr_matrix((data, (rows, cols)),
                                     shape=(len(user_to_idx), len(tag_to_idx)))

        # 标准化数据
        scaler = StandardScaler(with_mean=False)
        user_features = scaler.fit_transform(user_tag_sparse)

        # 降维和聚类
        pca = IncrementalPCA(n_components=min(20, len(tags) - 1), batch_size=1000)
        user_features_reduced = pca.fit_transform(user_features.toarray())

        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=1000)
        user_clusters = kmeans.fit_predict(user_features_reduced)

        # 将聚类结果添加到用户数据中
        users_df['cluster'] = user_clusters[:len(users_df)]

        # 保存结果和可视化
        os.makedirs('results', exist_ok=True)
        plot_path = plot_user_clusters(user_clusters, user_features_reduced, n_clusters)
        users_df.to_csv('data/users_clustered.csv', index=False)

        return {
            "data": users_df[['id', 'age', 'cluster']].to_dict('records'),
            "plot_path": plot_path
        }

    except Exception as e:
        logging.error(f"用户聚类失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"用户聚类失败: {str(e)}")