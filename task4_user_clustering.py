# -*- coding: utf-8 -*-
import time
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import IncrementalPCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import os
import logging

# from PyQt6.QtGui import QPixmap # 在非GUI环境下不需要导入

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
        t1 = time.time()
        # 确保 results 和 data 目录存在
        os.makedirs('results', exist_ok=True)
        os.makedirs('data', exist_ok=True)

        # 加载数据
        users_df = pd.read_csv('data/users.csv')
        videos_df = pd.read_csv('data/videos.csv')
        operations_df = pd.read_csv('data/operations.csv')

        # ... (中间的用户-标签矩阵构建、标准化、PCA降维等代码不变) ...
        # 确保 'id' 在 users_df 中
        if 'id' not in users_df.columns:
            users_df['id'] = range(len(users_df))

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

        # 确保 user_ids 的顺序与矩阵行序对应
        unique_user_ids = user_tag_counts['user_id'].unique()
        user_to_idx = {user_id: idx for idx, user_id in enumerate(unique_user_ids)}
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
        pca = IncrementalPCA(n_components=min(20, user_features.shape[1] - 1), batch_size=1000)
        user_features_reduced = pca.fit_transform(user_features.toarray())

        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=1000, n_init=3)
        user_clusters = kmeans.fit_predict(user_features_reduced)

        # 关键修改：将聚类结果映射回原始 user_id
        cluster_map_df = pd.DataFrame({
            'user_id_temp': unique_user_ids,
            'cluster': user_clusters
        })

        # 将聚类结果合并到原始 users_df
        users_df_clustered = users_df.merge(
            cluster_map_df, left_on='id', right_on='user_id_temp', how='left'
        ).drop(columns=['user_id_temp'])

        # 对于没有交互数据而没有聚类标签的用户，填充一个默认值（如 -1）
        users_df_clustered['cluster'] = users_df_clustered['cluster'].fillna(-1).astype(int)

        # 保存结果到 data 文件夹，供后续步骤读取
        output_path = 'data/users_clustered.csv'
        users_df_clustered.to_csv(output_path, index=False)
        logging.info(f"用户聚类结果已保存至: {output_path}")

        # 保存可视化
        plot_path = plot_user_clusters(user_clusters, user_features_reduced, n_clusters)

        t2 = time.time()
        print(f"task4模拟耗时: {t2 - t1:.4f} 秒")
        return {
            "data": users_df_clustered[['id', 'age', 'cluster']].head(10).to_dict('records'),
            "plot_path": plot_path
        }

    except Exception as e:
        logging.error(f"用户聚类失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"用户聚类失败: {str(e)}")