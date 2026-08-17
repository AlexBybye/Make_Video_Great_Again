# -*- coding: utf-8 -*-
# task4_user_clustering.py — 用户聚类分析
# 使用自建 CSRSparseMatrix 构建用户-标签矩阵, 替代 scipy CSR + pandas 扫描
# 聚类算法仍用 sklearn (纯数值计算, 无数据结构替代必要)
# 数据结构: CSRSparseMatrix + HashMap

import time
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import IncrementalPCA
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import logging
from ds.data_store import DataStore

logging.basicConfig(filename='results/user_clustering.log', level=logging.INFO)

# 暗色主题
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'Heiti TC', 'STHeiti', 'Arial Unicode MS'],
    'axes.unicode_minus': False,
    'figure.facecolor': '#0D0D1A',
    'axes.facecolor': '#0D0D1A',
    'axes.edgecolor': '#333355',
    'axes.labelcolor': '#AAAACC',
    'text.color': '#DDDDEE',
    'xtick.color': '#8888AA',
    'ytick.color': '#8888AA',
    'grid.color': '#1E1E3A',
    'grid.alpha': 0.4,
})


def plot_user_clusters(labels, reduced_data, n_clusters):
    fig, ax = plt.subplots(figsize=(11, 8))
    fig.patch.set_facecolor('#0D0D1A')
    ax.set_facecolor('#0D0D1A')

    scatter = ax.scatter(reduced_data[:, 0], reduced_data[:, 1],
                          c=labels, cmap='plasma', alpha=0.75, s=12,
                          edgecolor='none', linewidth=0)

    ax.set_title(f'用户兴趣聚类分布 (k={n_clusters})', fontsize=15,
                 fontweight='bold', color='#FFFFFF', pad=14)
    ax.set_xlabel('主成分 1', fontsize=12, color='#AAAACC')
    ax.set_ylabel('主成分 2', fontsize=12, color='#AAAACC')
    ax.tick_params(colors='#8888AA', labelsize=9)
    ax.grid(True, alpha=0.25, linewidth=0.4)

    cbar = fig.colorbar(scatter, ax=ax, label='聚类标签')
    cbar.ax.yaxis.label.set_color('#AAAACC')
    cbar.ax.tick_params(colors='#8888AA')
    cbar.outline.set_edgecolor('#333355')

    fig.tight_layout()
    plot_path = 'results/user_clusters.png'
    fig.savefig(plot_path, dpi=150, facecolor='#0D0D1A', bbox_inches='tight')
    plt.close(fig)
    return plot_path


def cluster_users(n_clusters=10):
    """基于自建 CSRSparseMatrix + sklearn 的用户聚类"""
    try:
        t1 = time.time()
        os.makedirs('results', exist_ok=True)
        os.makedirs('data', exist_ok=True)

        store = DataStore()

        # 使用自建 CSRSparseMatrix 转 numpy 用于 sklearn
        csr = store.user_tag_matrix
        user_ids = store._user_tag_users

        n_users = csr.n_rows
        n_tags = csr.n_cols

        # 从 CSR 提取 dense 矩阵 (sklearn 需要)
        user_features = np.zeros((n_users, n_tags))
        for i in range(n_users):
            cols, vals = csr.get_row(i)
            for c, v in zip(cols, vals):
                user_features[i, c] = v

        logging.info(f"[Task4] 使用自建 CSR 构建 {n_users}x{n_tags} 特征矩阵")

        # 标准化 + PCA + KMeans
        scaler = StandardScaler(with_mean=False)
        user_features_scaled = scaler.fit_transform(user_features)

        pca = IncrementalPCA(n_components=min(20, n_tags - 1), batch_size=1000)
        user_features_reduced = pca.fit_transform(user_features_scaled)

        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=1000, n_init=3)
        user_clusters = kmeans.fit_predict(user_features_reduced)

        # 构建 cluster_map: HashMap<int, int>
        cluster_map = {}
        for i, uid in enumerate(user_ids):
            cluster_map[int(uid)] = int(user_clusters[i])

        # 从 HashMap 获取用户信息并合并聚类结果
        import csv
        users_with_cluster = []
        all_user_ids = store.users_map.keys()
        for uid in all_user_ids:
            u = store.users_map.get(uid)
            if u is None:
                continue
            cluster = cluster_map.get(int(uid), -1)
            users_with_cluster.append({
                'id': int(uid),
                'age': u.get('age', ''),
                'gender': u.get('gender', ''),
                'cluster': cluster
            })

        # 保存 CSV (兼容后续流程)
        import csv as csv_writer
        output_path = 'data/users_clustered.csv'
        fieldnames = ['id', 'age', 'gender', 'cluster']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            w = csv_writer.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(users_with_cluster)
        logging.info(f"用户聚类结果已保存至: {output_path}")

        # 可视化
        plot_path = plot_user_clusters(user_clusters, user_features_reduced, n_clusters)

        t2 = time.time()
        print(f"task4耗时 (自建数据结构): {t2 - t1:.4f} 秒")

        # 返回前10条
        preview = [{'id': u['id'], 'age': u['age'], 'cluster': u['cluster']}
                   for u in users_with_cluster[:10]]

        return {
            "data": preview,
            "plot_path": plot_path
        }

    except Exception as e:
        logging.error(f"用户聚类失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"用户聚类失败: {str(e)}")
