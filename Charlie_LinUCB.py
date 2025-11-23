# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import logging
import time
import os

logging.basicConfig(filename='results/rl_bandit.log', level=logging.INFO)


class LinUCBBandit:
    """
    基于 LinUCB (Contextual Bandit) 的簇级动态探索模块。
    使用簇 Embedding 作为上下文，动态调整 '用户簇 x 视频簇' 对的探索权重。
    """

    def __init__(self, alpha=0.5, embedding_dim=20,
                 user_emb_path='results/user_cluster_embeddings.csv',
                 video_emb_path='results/video_cluster_embeddings.csv'):
        """
        初始化 Bandit 参数存储和加载 Embedding。

        :param alpha: 探索超参数，控制 UCB 探索项的权重。
        :param embedding_dim: 簇 Embedding 的维度。
        """
        self.alpha = alpha
        self.context_dim = embedding_dim * 2
        self.arm_metrics = {}

        # 1. 加载 Embedding (假设它们已由模块一生成并保存)
        try:
            self.E_CU = pd.read_csv(user_emb_path, index_col='user_cluster_id')
            self.E_CV = pd.read_csv(video_emb_path, index_col='video_cluster_id')

            # 检查维度匹配
            if self.E_CU.shape[1] != embedding_dim or self.E_CV.shape[1] != embedding_dim:
                logging.warning("实际 Embedding 维度与传入的 embedding_dim 不匹配！")
                self.context_dim = self.E_CU.shape[1] + self.E_CV.shape[1]

            logging.info(f"LinUCBBandit 加载 Embedding 成功。Context 维度: {self.context_dim}")

        except FileNotFoundError as e:
            logging.error(f"加载 Embedding 文件失败: {e}. 请确保先运行 get_cluster_embeddings。")
            raise FileNotFoundError("Embedding 文件缺失，无法运行 Bandit 模块。")
        except Exception as e:
            logging.error(f"加载 Embedding 过程中发生错误: {e}")
            raise RuntimeError(f"加载 Embedding 失败: {e}")

    def _get_arm_params(self, arm_id):
        """获取或初始化给定臂 (C_U, C_V) 的 A 和 b 矩阵/向量"""
        if arm_id not in self.arm_metrics:
            # 初始化 A 矩阵为单位矩阵 I
            A = np.identity(self.context_dim)
            # 初始化 b 向量为零向量
            b = np.zeros(self.context_dim)
            self.arm_metrics[arm_id] = {'A': A, 'b': b}
        return self.arm_metrics[arm_id]

    def _get_context_vector(self, user_cluster_id, video_cluster_id):
        """构造上下文向量 X"""
        try:
            # 从 DataFrame 中按索引查询并获取 NumPy 数组
            u_emb = self.E_CU.loc[user_cluster_id].values
            v_emb = self.E_CV.loc[video_cluster_id].values
            # X = [E_CU || E_CV]
            X = np.concatenate([u_emb, v_emb])
            return X
        except KeyError:
            logging.warning(f"无法获取簇 Embedding: ({user_cluster_id}, {video_cluster_id}).")
            return None

    def get_ucb_score(self, user_cluster_id, video_cluster_id):
        """
        计算 UCB 分数，作为动态探索权重。

        :return: UCB Score (float) 或 0 (如果 Embedding 不存在)。
        """
        arm_id = (user_cluster_id, video_cluster_id)
        X = self._get_context_vector(user_cluster_id, video_cluster_id)
        if X is None:
            return 0.0

        metrics = self._get_arm_params(arm_id)
        A = metrics['A']
        b = metrics['b']

        # 求解 theta: theta = A^(-1) * b
        try:
            A_inv = np.linalg.inv(A)
        except np.linalg.LinAlgError:
            # 如果 A 矩阵不可逆 (极少发生，通常是初始化后数据太少导致)，返回默认探索分
            logging.error(f"矩阵 A 不可逆，臂 {arm_id} 无法计算 UCB。")
            return self.alpha * 10  # 给予一个较大的默认探索分

        theta = A_inv @ b

        # 预测收益 (Exploitation Term): mu = X^T * theta
        mu = X.T @ theta

        # 探索项 (Exploration Term): s = alpha * sqrt(X^T * A^(-1) * X)
        s = self.alpha * np.sqrt(X.T @ A_inv @ X)

        ucb_score = mu + s

        # 确保分数在合理范围内，例如非负
        return max(0, ucb_score)

    def update_feedback(self, user_cluster_id, video_cluster_id, reward):
        """
        根据用户的实时反馈 (Reward) 更新 Bandit 模型参数。

        :param reward: 用户的实际奖励 (0 到 1 之间的浮点数，例如完播率 x 互动率)。
        """
        arm_id = (user_cluster_id, video_cluster_id)
        X = self._get_context_vector(user_cluster_id, video_cluster_id)
        if X is None:
            return

        metrics = self._get_arm_params(arm_id)

        # 1. 更新 A 矩阵: A <- A + X * X^T
        metrics['A'] += np.outer(X, X)

        # 2. 更新 b 向量: b <- b + Reward * X
        metrics['b'] += reward * X

        logging.info(f"更新臂 {arm_id}: Reward={reward:.4f}")


def apply_rl_dynamic_weight(bandit, user_cluster_id, candidates):
    """
    将 Bandit 模型输出的 UCB 分数转化为动态探索权重，并作用于排序。

    :param bandit: LinUCBBandit 实例。
    :param user_cluster_id: 当前用户的簇 ID。
    :param candidates: 包含 (video_id, video_cluster_id, base_score) 的列表。
    :return: 排序后的候选列表 (video_id, final_score)。
    """
    ranked_list = []

    for video_id, cluster_id, base_score in candidates:
        ucb_score = bandit.get_ucb_score(user_cluster_id, cluster_id)

        # 策略：将 UCB score 映射为一个动态权重 (例如，通过 Sigmoid 或简单线性映射)
        # 这里的 UCB score 被视为该簇对的“探索/收益潜力”

        # 简化策略：将 UCB score 直接乘以基础分数，作为对该簇对的倾斜权重
        # 实际复杂策略会用 UCB 来调节 exploration rate α

        # 动态权重：使用 tanh 激活函数将 UCB score 映射到 (0, 1) 附近，作为探索倾向
        exploration_weight = np.tanh(ucb_score)

        final_score = base_score * (1 + exploration_weight)  # 增加倾向性

        ranked_list.append({
            'video_id': video_id,
            'cluster_id': cluster_id,
            'final_score': final_score,
            'ucb_score': ucb_score
        })

    ranked_list.sort(key=lambda x: x['final_score'], reverse=True)
    return ranked_list


# -------------------------- 模块集成演示 (非主要功能) --------------------------
if __name__ == '__main__':
    # 注意：需要确保 results/user_cluster_embeddings.csv 和 videos_cluster_embeddings.csv 存在
    try:
        # 假设 embedding_dim 为 20
        EMBEDDING_DIM = 20

        # 初始化 Bandit (它会自动加载 Embedding)
        rl_bandit = LinUCBBandit(alpha=0.2, embedding_dim=EMBEDDING_DIM)

    except FileNotFoundError:
        print("错误：请先运行聚类和 get_cluster_embeddings 函数生成 Embedding 文件。")
        exit()

    # 模拟用户 (C_U=1) 的推荐列表
    user_id = 1

    # 模拟两个视频簇作为候选：
    # C_V=5 (高奖励簇，应被更多利用)
    # C_V=10 (低奖励簇，应被减少利用)
    candidates_list = [
        (101, 5, 0.5),  # V1: 簇 5 (基础分 0.5)
        (201, 10, 0.6),  # V2: 簇 10 (基础分 0.6, 初始可能靠前)
    ]

    print("--- 簇级 RL 动态调整演示 (用户簇 1) ---")

    for i in range(15):
        # 1. 决策：根据 UCB 排序
        ranking = apply_rl_dynamic_weight(rl_bandit, user_id, candidates_list)
        top_item = ranking[0]

        # 2. 模拟奖励（假设 C_U=1 对 C_V=5 的兴趣高）
        reward = 0.0
        if top_item['cluster_id'] == 5:
            reward = 0.9  # 高奖励
        elif top_item['cluster_id'] == 10:
            reward = 0.2  # 低奖励

        reward += np.random.normal(0, 0.05)
        reward = np.clip(reward, 0, 1)

        # 3. 更新
        rl_bandit.update_feedback(user_id, top_item['cluster_id'], reward)

        # 4. 打印当前状态
        ucb_5 = [item['ucb_score'] for item in ranking if item['cluster_id'] == 5][0]
        ucb_10 = [item['ucb_score'] for item in ranking if item['cluster_id'] == 10][0]

        print(f"轮 {i + 1}: 选中簇 {top_item['cluster_id']}. 奖励={reward:.3f}")
        print(f"    -> UCB(C5): {ucb_5:.4f}, UCB(C10): {ucb_10:.4f}. Top Score: {top_item['final_score']:.4f}")
        time.sleep(0.01)

    print(
        "\n观察结果：随着迭代，高奖励臂 (C_U=1 x C_V=5) 的 UCB 分数会稳定在高位，即使它的基础分较低，也能通过 RL 权重获得更高的最终排序分数，实现动态利用。")