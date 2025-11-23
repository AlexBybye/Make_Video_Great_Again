# -*- coding: utf-8 -*-
import time
import pandas as pd
import numpy as np
import logging

logging.basicConfig(filename='results/cold_start.log', level=logging.INFO)


class ColdStartRanker:
    """
    基于 Thompson Sampling (TS) 的簇内冷启动再排序模块。
    用于新视频在所属视频簇内的快速探索。
    """

    def __init__(self, initial_alpha=1, initial_beta=1, threshold_N=5000):
        """
        初始化 TS 参数存储。
        :param initial_alpha: 初始正例计数 (平滑)。
        :param initial_beta: 初始负例计数 (平滑)。
        :param threshold_N: 退出冷启动所需的曝光阈值。
        """
        # 使用字典模拟实时存储：Key: video_cluster_id, Value: {'alpha': int, 'beta': int, 'N': int}
        self.cluster_metrics = {}
        self.initial_alpha = initial_alpha
        self.initial_beta = initial_beta
        self.threshold_N = threshold_N

    def _get_metrics(self, cluster_id):
        """获取或初始化给定簇的指标"""
        if cluster_id not in self.cluster_metrics:
            self.cluster_metrics[cluster_id] = {
                'alpha': self.initial_alpha,
                'beta': self.initial_beta,
                'N': 0
            }
        return self.cluster_metrics[cluster_id]

    def get_ts_score(self, video_cluster_id):
        """
        根据 Thompson Sampling 逻辑，为视频簇生成探索分数。

        :param video_cluster_id: 待评分视频所属的视频簇 ID。
        :return: TS 分数 (float) 或 None (如果已退出冷启动)。
        """
        metrics = self._get_metrics(video_cluster_id)

        # 检查是否满足退出条件 (例如曝光量达到阈值)
        if metrics['N'] >= self.threshold_N:
            # 退出冷启动，返回 None 或一个代表稳定的分数，这里返回 None 代表进入精排
            return None

        # Thompson Sampling 核心：从 Beta 分布中采样概率
        # Beta(alpha, beta) 的均值是 alpha / (alpha + beta)
        score = np.random.beta(metrics['alpha'], metrics['beta'])

        logging.debug(f"簇 {video_cluster_id}: 采样分数 {score:.4f}, (α={metrics['alpha']}, β={metrics['beta']})")
        return score

    def update_feedback(self, video_cluster_id, is_positive):
        """
        模拟实时反馈，更新视频簇的 alpha/beta 值。

        :param video_cluster_id: 发生交互的视频簇 ID。
        :param is_positive: True (积极互动，如完播/点赞), False (消极互动/跳过)。
        """
        metrics = self._get_metrics(video_cluster_id)

        # 更新曝光量 N
        metrics['N'] += 1

        if is_positive:
            metrics['alpha'] += 1
        else:
            metrics['beta'] += 1

        logging.info(
            f"更新簇 {video_cluster_id}: Positive={is_positive}. 新 (α={metrics['alpha']}, β={metrics['beta']}, N={metrics['N']})")

    def simulate_ranking(self, new_video_cluster_ids, other_scores=None):
        """
        模拟推荐列表的生成和排序。

        :param new_video_cluster_ids: 待冷启动的新视频簇 ID 列表。
        :param other_scores: 其他（非冷启动）视频的精排分数，用于对比。
        :return: 排序后的 (cluster_id, final_score) 列表。
        """
        ranking_list = []

        # 1. 计算冷启动视频的 TS 分数
        for cluster_id in new_video_cluster_ids:
            ts_score = self.get_ts_score(cluster_id)
            if ts_score is not None:
                ranking_list.append((cluster_id, ts_score, "ColdStart"))
            else:
                # 假设已退出冷启动，给一个基础的平均分数
                avg_score = self._get_metrics(cluster_id)['alpha'] / (
                            self._get_metrics(cluster_id)['alpha'] + self._get_metrics(cluster_id)['beta'])
                ranking_list.append((cluster_id, avg_score, "GlobalRank"))

        # 2. 如果提供了其他分数，也加入列表
        if other_scores:
            ranking_list.extend(other_scores)

        # 3. 排序 (分数越高越靠前)
        ranking_list.sort(key=lambda x: x[1], reverse=True)

        return ranking_list


# -------------------------- 模拟演示 --------------------------
if __name__ == '__main__':
    ranker = ColdStartRanker(initial_alpha=10, initial_beta=10)  # 启动一个 ranker

    # 假设我们有三个新上线的视频簇 ID
    new_clusters = [1, 5, 8]

    print("--- 初始探索阶段 ---")
    for i in range(5):
        # 模拟推荐列表
        ranking = ranker.simulate_ranking(new_clusters)
        print(f"第 {i + 1} 轮排序结果 (前3)：{[f'簇{c}: {s:.4f}' for c, s, _ in ranking[:3]]}")

        # 模拟用户互动：假设用户总是点击排名第一的簇
        top_cluster = ranking[0][0]
        # 假设簇 5 表现较好 (70% 积极)，簇 1 表现一般 (50%)，簇 8 表现差 (30%)
        is_pos = False
        if top_cluster == 5:
            is_pos = np.random.rand() < 0.7
        elif top_cluster == 1:
            is_pos = np.random.rand() < 0.5
        elif top_cluster == 8:
            is_pos = np.random.rand() < 0.3

        ranker.update_feedback(top_cluster, is_pos)
        time.sleep(0.05)  # 模拟延迟

    # 打印最终参数变化
    print("\n--- 5轮迭代后参数 ---")
    for cluster_id in new_clusters:
        metrics = ranker._get_metrics(cluster_id)
        # TS 分数的期望值 (真实CTR估计)
        avg_ctr = metrics['alpha'] / (metrics['alpha'] + metrics['beta'])
        print(
            f"簇 {cluster_id}: N={metrics['N']}, Alpha={metrics['alpha']}, Beta={metrics['beta']}, 估计CTR={avg_ctr:.4f}")

    print("\n观察结果：TS 分布的均值会逐渐收敛到真实CTR，导致表现好的簇（簇5）的采样分数逐渐高于表现差的簇（簇8）。")