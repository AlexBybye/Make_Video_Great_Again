# -*- coding: utf-8 -*-
# task2_recommend_videos.py — 视频推荐 + 推荐路径解释
# 数据结构: HashMap + Graph (BFS 路径回溯) + MaxHeap (Top-K)

import time
import logging
import numpy as np
from ds.data_store import DataStore
from ds.max_heap import MaxHeap

TOP_K_SIMILAR = 20


def recommend_videos(target_user_id, use_enhanced=False):
    """基于 Graph BFS + MaxHeap Top-K 的协同过滤推荐, 含路径解释, 可选 TS/LinUCB 增强"""

    t1 = time.time()
    store = DataStore()

    if not store.user_exists(target_user_id):
        raise ValueError(f"用户ID {target_user_id} 不存在")

    mode_str = "增强模式" if use_enhanced else "标准模式"
    logging.info(f"[Task2] 使用 Graph + MaxHeap 为用户 {target_user_id} 生成推荐 ({mode_str})")

    # 1. HashMap O(1) 获取已观看视频
    user_viewed_videos = store.get_user_viewed_videos(target_user_id)

    # 2. Graph BFS: 距离=2 的相似用户
    similar_users = store.get_similar_users_bfs(target_user_id, max_depth=2)

    if not similar_users:
        raise ValueError("没有找到相似用户，无法推荐")

    # 3. HashMap 聚合候选视频分数
    candidate_scores = {}
    for other_uid, sim in similar_users.items():
        ops = store.get_user_operations(other_uid)
        for op in ops:
            vid = op['video_id']
            if vid in user_viewed_videos:
                continue
            weight = sim * (2.0 if op['liked'] == 1 else 1.0)
            candidate_scores[vid] = candidate_scores.get(vid, 0) + weight

    if not candidate_scores:
        raise ValueError("没有找到合适的推荐视频")

    # 4. 增强模式: 应用 TS + LinUCB 动态权重
    ts_boosts = {}
    linucb_boosts = {}
    if use_enhanced:
        try:
            from ds.bandit_store import BanditStore
            bs = BanditStore()
            bs.ensure_init()
            for vid in candidate_scores:
                base = candidate_scores[vid]
                # TS 探索加成 (新簇视频获得更高加成)
                ts_score = bs.get_ts_score(vid)
                if ts_score is not None:
                    ts_boost = 1.0 + ts_score  # TS 分数越高, 加成越大
                    ts_boosts[vid] = f"+{ts_score:.2f}"
                else:
                    ts_boost = 1.0
                    ts_boosts[vid] = "N/A"

                # LinUCB 动态权重
                lw = bs.get_linucb_weight(target_user_id, vid)
                linucb_boost = 1.0 + np.tanh(lw)  # tanh 映射到 (0,2)
                linucb_boosts[vid] = f"+{np.tanh(lw):.2f}"

                candidate_scores[vid] = base * ts_boost * linucb_boost
        except Exception as e:
            logging.warning(f"[Task2] 增强模式初始化失败: {e}")

    # 5. MaxHeap 提取 Top-10
    heap = MaxHeap()
    for vid, score in candidate_scores.items():
        heap.push(score, vid)

    top_10 = heap.top_k(10)

    # 6. 构建结果
    result = []
    for score, vid in top_10:
        v = store.get_video(vid)
        tag = v['tag'] if v else '未知'

        explanation = store.explain_recommendation(target_user_id, int(vid))
        if explanation:
            reason = (f"你观看过「{explanation['shared_tag']}」类视频(#{explanation['shared_video']}), "
                      f"兴趣相似用户#{explanation['similar_user']} 也观看了该视频")
        else:
            reason = "基于协同过滤算法推荐"

        result.append({
            "Video_ID": int(vid),
            "label": tag,
            "Overall_rating": round(float(score), 2),
            "reason": reason,
            "enhanced": use_enhanced,
            "ts_boost": ts_boosts.get(vid, ""),
            "linucb_boost": linucb_boosts.get(vid, "")
        })

    t2 = time.time()
    print(f"task2耗时 ({mode_str}): {t2 - t1:.4f} 秒")
    return result
