# -*- coding: utf-8 -*-
# task5_video_clustering.py — 视频聚类分析
# 使用自建 HashMap + CSRSparseMatrix, 采样后再转 dense 避免 OOM
# 数据结构: HashMap + CSRSparseMatrix (dok→csr)

import time
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.preprocessing import normalize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import logging
from ds.data_store import DataStore
from ds.sparse_matrix import CSRSparseMatrix

logging.basicConfig(filename='results/clustering.log', level=logging.INFO)

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


def plot_clusters(labels, reduced_data, n_clusters):
    fig, ax = plt.subplots(figsize=(11, 8))
    fig.patch.set_facecolor('#0D0D1A')
    ax.set_facecolor('#0D0D1A')

    scatter = ax.scatter(reduced_data[:, 0], reduced_data[:, 1],
                          c=labels, cmap='cividis', alpha=0.8, s=14,
                          edgecolor='none')

    for i in range(n_clusters):
        mask = labels == i
        if mask.sum() > 0:
            cx, cy = reduced_data[mask, 0].mean(), reduced_data[mask, 1].mean()
            ax.scatter(cx, cy, c='#FFFFFF', s=80, marker='X', edgecolor='#FB7299',
                       linewidth=1.2, zorder=5)
            ax.annotate(f'{i}', (cx, cy), color='#FFFFFF', fontsize=9, fontweight='bold',
                        ha='center', va='bottom', xytext=(0, 8), textcoords='offset points')

    ax.set_title(f'视频内容聚类分布 (k={n_clusters})', fontsize=15,
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
    plot_path = 'results/video_clusters.png'
    fig.savefig(plot_path, dpi=150, facecolor='#0D0D1A', bbox_inches='tight')
    plt.close(fig)
    return plot_path


def _csr_to_dense_rows(csr, row_indices, n_cols):
    """只将 CSR 中指定的行转为 dense, 避免全量 dense 化"""
    n_rows = len(row_indices)
    dense = np.zeros((n_rows, n_cols), dtype=np.float32)
    for out_i, src_i in enumerate(row_indices):
        cols, vals = csr.get_row(src_i)
        for c, v in zip(cols, vals):
            dense[out_i, c] = v
    return dense


def cluster_videos(n_clusters=5, sample_size=5000):
    try:
        t1 = time.time()
        os.makedirs('results', exist_ok=True)
        os.makedirs('data', exist_ok=True)

        store = DataStore()

        # 有交互的视频和用户
        video_ids = sorted(store.ops_by_video.keys())
        user_ids = sorted(store.ops_by_user.keys())

        video_to_idx = {vid: i for i, vid in enumerate(video_ids)}
        user_to_idx = {uid: i for i, uid in enumerate(user_ids)}

        # 构建 DOK: key=(video_idx, user_idx) — 视频为行
        dok = {}
        for uid in user_ids:
            ops = store.get_user_operations(uid)
            ui = user_to_idx[uid]
            for op in ops:
                vid = op['video_id']
                vi = video_to_idx.get(vid)
                if vi is None:
                    continue
                weight = 2.0 if op['liked'] == 1 else 1.0
                dok[(vi, ui)] = dok.get((vi, ui), 0) + weight

        n_videos = len(video_ids)
        n_users = len(user_ids)

        # 自建 CSR: 视频×用户 (稀疏)
        video_user_csr = CSRSparseMatrix.from_dok(dok, n_videos, n_users)
        logging.info(f"[Task5] CSR 交互矩阵: {video_user_csr}")

        # 过滤空行 + 采样 — 全在 CSR 上操作, 不转 dense
        nonempty_rows = []
        for i in range(n_videos):
            if len(video_user_csr.get_row(i)[0]) > 0:
                nonempty_rows.append(i)

        if len(nonempty_rows) == 0:
            raise RuntimeError("没有可用于聚类的视频")

        # 采样
        if sample_size and len(nonempty_rows) > sample_size:
            sampled = sorted(np.random.choice(nonempty_rows, sample_size, replace=False))
        else:
            sampled = nonempty_rows

        sampled_video_ids = [video_ids[i] for i in sampled]
        logging.info(f"[Task5] 采样 {len(sampled)} 个视频 (共 {len(nonempty_rows)} 个有效)")

        # 只把采样的行转 dense (5000 × 10000 = 50M, 可接受)
        dense = _csr_to_dense_rows(video_user_csr, sampled, n_users)

        # 归一化
        dense = normalize(dense, norm='l2', axis=1)

        # 降维 + 聚类
        n_comp = min(20, dense.shape[1] - 1, dense.shape[0] - 1)
        svd = TruncatedSVD(n_components=n_comp, random_state=42)
        reduced = svd.fit_transform(dense)

        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=500, n_init=3)
        labels = kmeans.fit_predict(reduced)

        # 构建聚类结果
        cluster_map = {}
        for i, vid in enumerate(sampled_video_ids):
            cluster_map[int(vid)] = int(labels[i])

        import csv as csv_writer
        all_videos = []
        for vid in store.videos_map.keys():
            v = store.videos_map.get(vid)
            if v is None:
                continue
            all_videos.append({
                'id': int(vid),
                'tag': v.get('tag', ''),
                'views': int(v.get('views', 0)),
                'likes': int(v.get('likes', 0)),
                'title': str(v.get('title', '')),
                'cluster': cluster_map.get(int(vid), n_clusters - 1)
            })

        output_path = 'data/videos_clustered.csv'
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            w = csv_writer.DictWriter(f, fieldnames=['id', 'tag', 'views', 'likes', 'title', 'cluster'])
            w.writeheader()
            w.writerows(all_videos)
        logging.info(f"视频聚类结果已保存至: {output_path}")

        # 可视化: 2D PCA
        pca_viz = PCA(n_components=2, random_state=42)
        viz_data = pca_viz.fit_transform(reduced)
        plot_path = plot_clusters(labels, viz_data, n_clusters)

        t2 = time.time()
        print(f"task5耗时 (自建数据结构): {t2 - t1:.4f} 秒")

        preview = [{'id': v['id'], 'tag': v['tag'], 'views': v['views'],
                     'likes': v['likes'], 'cluster': v['cluster']}
                   for v in all_videos[:10]]

        return {
            "data": preview,
            "plot_path": plot_path
        }

    except Exception as e:
        logging.error(f"聚类失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"视频聚类失败: {str(e)}")
