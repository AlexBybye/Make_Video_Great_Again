# -*- coding: utf-8 -*-
# ds/bandit_store.py — Bandit 持久化层
# 全局单例: Thompson Sampling + LinUCB, 支持交互式训练 + 可视化

import os
import time
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'Heiti TC', 'STHeiti', 'Arial Unicode MS'],
    'axes.unicode_minus': False,
})
from scipy.stats import beta as beta_dist

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BanditStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def init(self):
        if self._initialized:
            return

        from Beta_Thompson_Sampling import ColdStartRanker
        from Charlie_LinUCB import LinUCBBandit

        self.ts_ranker = ColdStartRanker(initial_alpha=1, initial_beta=1, threshold_N=1000)

        # LinUCB 延迟初始化 (需要 SVD embedding 文件)
        self.linucb_bandit = None
        self.linucb_ready = False

        emb_path = os.path.join(BASE_DIR, 'results', 'user_cluster_embeddings.csv')
        if os.path.exists(emb_path):
            try:
                self.linucb_bandit = LinUCBBandit(alpha=0.2, embedding_dim=20)
                self.linucb_ready = True
                logging.info("[BanditStore] LinUCB 初始化成功")
            except Exception as e:
                logging.warning(f"[BanditStore] LinUCB 初始化失败: {e}")

        # 加载簇映射
        self.user_cluster_map = {}  # user_id → cluster_id
        self.video_cluster_map = {}  # video_id → cluster_id
        self._load_cluster_maps()

        # 交互训练追踪
        self.round_count = 0
        self.ts_history = []  # [(round, cluster_id, alpha, beta, ctr), ...]
        self.linucb_history = []  # [(round, arm, ucb_score), ...]
        self.current_user_id = None
        self.current_candidates = []

        self._initialized = True
        logging.info("[BanditStore] 初始化完成")

    def _load_cluster_maps(self):
        import pandas as pd
        users_path = os.path.join(BASE_DIR, 'data', 'users_clustered.csv')
        videos_path = os.path.join(BASE_DIR, 'data', 'videos_clustered.csv')

        if os.path.exists(users_path):
            df = pd.read_csv(users_path)
            for _, row in df.iterrows():
                self.user_cluster_map[int(row['id'])] = int(row['cluster'])

        if os.path.exists(videos_path):
            df = pd.read_csv(videos_path)
            for _, row in df.iterrows():
                self.video_cluster_map[int(row['id'])] = int(row['cluster'])

        logging.info(f"[BanditStore] 加载簇映射: {len(self.user_cluster_map)} 用户, {len(self.video_cluster_map)} 视频")

    def ensure_init(self):
        if not self._initialized:
            self.init()

    # ==================== TS 操作 ====================

    def get_ts_score(self, video_id):
        """获取视频所在簇的 TS 探索分数"""
        self.ensure_init()
        cluster_id = self.video_cluster_map.get(video_id)
        if cluster_id is None:
            return None
        return self.ts_ranker.get_ts_score(cluster_id)

    def get_cluster_ctr(self, cluster_id):
        """获取簇的估计 CTR"""
        self.ensure_init()
        metrics = self.ts_ranker._get_metrics(cluster_id)
        return metrics['alpha'] / (metrics['alpha'] + metrics['beta'])

    # ==================== LinUCB 操作 ====================

    def get_linucb_weight(self, user_id, video_id):
        """获取 (用户, 视频) 组合的 LinUCB 动态权重"""
        self.ensure_init()
        if not self.linucb_ready:
            return 0.0

        u_cluster = self.user_cluster_map.get(user_id)
        v_cluster = self.video_cluster_map.get(video_id)
        if u_cluster is None or v_cluster is None:
            return 0.0

        return self.linucb_bandit.get_ucb_score(u_cluster, v_cluster)

    # ==================== 反馈更新 ====================

    def apply_feedback(self, user_id, video_id, liked):
        """同时更新 TS 和 LinUCB"""
        self.ensure_init()
        self.round_count += 1

        v_cluster = self.video_cluster_map.get(video_id)
        u_cluster = self.user_cluster_map.get(user_id)

        # 1. 更新 TS
        if v_cluster is not None:
            self.ts_ranker.update_feedback(v_cluster, liked)
            metrics = self.ts_ranker._get_metrics(v_cluster)
            ctr = metrics['alpha'] / (metrics['alpha'] + metrics['beta'])
            self.ts_history.append({
                'round': self.round_count,
                'cluster': v_cluster,
                'alpha': metrics['alpha'],
                'beta': metrics['beta'],
                'N': metrics['N'],
                'ctr': round(ctr, 4)
            })

        # 2. 更新 LinUCB
        if self.linucb_ready and u_cluster is not None and v_cluster is not None:
            reward = 1.0 if liked else 0.0
            self.linucb_bandit.update_feedback(u_cluster, v_cluster, reward)
            ucb = self.linucb_bandit.get_ucb_score(u_cluster, v_cluster)
            self.linucb_history.append({
                'round': self.round_count,
                'arm': f"U{u_cluster}×V{v_cluster}",
                'ucb': round(float(ucb), 4),
                'reward': reward
            })

    # ==================== 交互式候选 ====================

    def pick_candidates(self, user_id=None, n=4):
        """为交互式训练选取候选视频"""
        self.ensure_init()
        from data_cache import DataCache

        ops = DataCache.load_operations()
        videos = DataCache.load_videos()

        if user_id is None:
            import random
            all_users = list(self.user_cluster_map.keys())
            user_id = random.choice(all_users[:500]) if all_users else 1

        self.current_user_id = user_id

        # 获取用户已观看的视频
        if ops is not None:
            viewed = set(ops[ops['user_id'] == user_id]['video_id'].values)
        else:
            viewed = set()

        # 选候选：部分已观看（作为正例参考），部分未观看
        candidates = []
        if videos is not None:
            unviewed = videos[~videos['id'].isin(viewed)]
            if len(unviewed) > 0:
                sample = unviewed.sample(min(n, len(unviewed)))
                for _, v in sample.iterrows():
                    vid = int(v['id'])
                    ts = self.get_ts_score(vid) or 0
                    lw = self.get_linucb_weight(user_id, vid)
                    candidates.append({
                        'video_id': vid,
                        'tag': str(v.get('tag', '未知')),
                        'views': int(v.get('views', 0)),
                        'likes': int(v.get('likes', 0)),
                        'ts_score': round(float(ts) if ts else 0, 4),
                        'linucb_weight': round(float(lw), 4),
                        'viewed': False
                    })

        self.current_candidates = candidates
        return {'user_id': user_id, 'candidates': candidates}

    # ==================== 状态查询 ====================

    def get_state(self):
        """返回当前完整状态给前端"""
        self.ensure_init()
        cluster_metrics = {}
        for cid in self.ts_ranker.cluster_metrics:
            m = self.ts_ranker.cluster_metrics[cid]
            ctr = m['alpha'] / (m['alpha'] + m['beta']) if (m['alpha'] + m['beta']) > 0 else 0
            cluster_metrics[int(cid)] = {
                'alpha': m['alpha'],
                'beta': m['beta'],
                'N': m['N'],
                'ctr': round(ctr, 4)
            }

        return {
            'round_count': self.round_count,
            'current_user_id': self.current_user_id,
            'linucb_ready': self.linucb_ready,
            'ts_clusters': cluster_metrics,
            'ts_history': self.ts_history[-20:],
            'linucb_history': self.linucb_history[-20:]
        }

    def reset(self):
        """重置所有状态"""
        from Beta_Thompson_Sampling import ColdStartRanker
        from Charlie_LinUCB import LinUCBBandit

        self.ts_ranker = ColdStartRanker(initial_alpha=1, initial_beta=1, threshold_N=1000)
        self.linucb_bandit = None
        self.linucb_ready = False

        emb_path = os.path.join(BASE_DIR, 'results', 'user_cluster_embeddings.csv')
        if os.path.exists(emb_path):
            try:
                self.linucb_bandit = LinUCBBandit(alpha=0.2, embedding_dim=20)
                self.linucb_ready = True
            except Exception:
                pass

        self.round_count = 0
        self.ts_history = []
        self.linucb_history = []
        self.current_user_id = None
        self.current_candidates = []
        logging.info("[BanditStore] 已重置")

    # ==================== 可视化 ====================

    def generate_ts_plot(self):
        """生成 TS Beta 分布图"""
        self.ensure_init()
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))

        x = np.linspace(0, 1, 500)
        # 取有数据的簇，按 N 排序取 Top-8
        active = [(cid, m) for cid, m in self.ts_ranker.cluster_metrics.items() if m['N'] > 0]
        active.sort(key=lambda x: x[1]['N'], reverse=True)
        top = active[:8]

        if not top:
            # 还没训练过，显示先验
            top = [(cid, self.ts_ranker._get_metrics(cid))
                   for cid in list(self.ts_ranker.cluster_metrics.keys())[:5]]

        colors = plt.cm.tab10(np.linspace(0, 1, len(top)))
        for (cid, m), color in zip(top, colors):
            a, b = m['alpha'], m['beta']
            y = beta_dist.pdf(x, a, b)
            ctr = a / (a + b)
            ax.plot(x, y, color=color, lw=2, alpha=0.85,
                    label=f'簇{cid} (α={a}, β={b}, CTR≈{ctr:.3f})')

        ax.set_xlabel('CTR (点击率)', fontsize=12)
        ax.set_ylabel('概率密度', fontsize=12)
        ax.set_title(f'Thompson Sampling — Beta 分布 (第{self.round_count}轮)', fontsize=14)
        ax.legend(loc='upper right', fontsize=9, framealpha=0.5)
        ax.set_xlim(0, 1)
        ax.grid(alpha=0.2)

        path = os.path.join(BASE_DIR, 'results', 'ts_beta_distribution.png')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.savefig(path, dpi=120, bbox_inches='tight', facecolor='#1a1a2e')
        plt.close(fig)
        return '/api/images/results/ts_beta_distribution.png'

    def generate_linucb_plot(self):
        """生成 LinUCB UCB 收敛图"""
        self.ensure_init()
        if not self.linucb_history:
            return None

        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # 按 arm 分组
        arms = {}
        for h in self.linucb_history:
            arm = h['arm']
            if arm not in arms:
                arms[arm] = {'rounds': [], 'ucb': [], 'reward': []}
            arms[arm]['rounds'].append(h['round'])
            arms[arm]['ucb'].append(h['ucb'])
            arms[arm]['reward'].append(h['reward'])

        colors = plt.cm.tab10(np.linspace(0, 1, len(arms)))
        for (arm, data), color in zip(arms.items(), colors):
            ax1.plot(data['rounds'], data['ucb'], 'o-', color=color, lw=2, markersize=6, label=arm)
        ax1.set_xlabel('训练轮次', fontsize=12)
        ax1.set_ylabel('UCB 分数', fontsize=12)
        ax1.set_title('LinUCB — UCB 分数收敛', fontsize=14)
        ax1.legend(fontsize=9, framealpha=0.5)
        ax1.grid(alpha=0.2)

        # 右图: 累计平均奖励
        for (arm, data), color in zip(arms.items(), colors):
            cum_reward = np.cumsum(data['reward']) / np.arange(1, len(data['reward']) + 1)
            ax2.plot(data['rounds'], cum_reward, '-', color=color, lw=2, label=f'{arm} 均奖励')
        ax2.set_xlabel('训练轮次', fontsize=12)
        ax2.set_ylabel('累计平均奖励', fontsize=12)
        ax2.set_title('累计平均奖励趋势', fontsize=14)
        ax2.legend(fontsize=9, framealpha=0.5)
        ax2.grid(alpha=0.2)
        ax2.set_ylim(0, 1.05)

        plt.tight_layout()
        path = os.path.join(BASE_DIR, 'results', 'linucb_convergence.png')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.savefig(path, dpi=120, bbox_inches='tight', facecolor='#1a1a2e')
        plt.close(fig)
        return '/api/images/results/linucb_convergence.png'

    def generate_ts_ctr_plot(self):
        """生成 TS 各簇 CTR 收敛图"""
        self.ensure_init()
        if not self.ts_history:
            return None

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))

        # 按簇分组
        clusters = {}
        for h in self.ts_history:
            cid = h['cluster']
            if cid not in clusters:
                clusters[cid] = {'rounds': [], 'ctr': []}
            clusters[cid]['rounds'].append(h['round'])
            clusters[cid]['ctr'].append(h['ctr'])

        colors = plt.cm.tab10(np.linspace(0, 1, len(clusters)))
        for (cid, data), color in zip(clusters.items(), colors):
            ax.plot(data['rounds'], data['ctr'], 'o-', color=color, lw=2, markersize=6, label=f'簇{cid}')

        ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.3, label='随机基线')
        ax.set_xlabel('训练轮次', fontsize=12)
        ax.set_ylabel('估计 CTR', fontsize=12)
        ax.set_title('Thompson Sampling — 各簇 CTR 收敛', fontsize=14)
        ax.legend(fontsize=9, framealpha=0.5)
        ax.grid(alpha=0.2)
        ax.set_ylim(0, 1)

        path = os.path.join(BASE_DIR, 'results', 'ts_ctr_convergence.png')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.savefig(path, dpi=120, bbox_inches='tight', facecolor='#1a1a2e')
        plt.close(fig)
        return '/api/images/results/ts_ctr_convergence.png'
