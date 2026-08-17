# app.py - Flask Web 后端
import os
import sys
import logging
import time
import numpy as np

# 设置 matplotlib 非交互后端（必须在 import matplotlib.pyplot 之前）
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'Heiti TC', 'STHeiti', 'Arial Unicode MS'],
    'axes.unicode_minus': False,
})

from flask import Flask, render_template, request, jsonify, send_from_directory

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'web', 'templates'),
            static_folder=os.path.join(BASE_DIR, 'web', 'static'))

# ============================================================
# 启动初始化
# ============================================================
data_init_error = None

try:
    from data_manager import DataManager
    DataManager()
    logging.info("数据管理器初始化成功")
except Exception as e:
    data_init_error = str(e)
    logging.error(f"数据初始化失败: {e}")

# 初始化自建数据结构层 (复用 DataCache 的 DataFrame, 避免重复读文件)
try:
    from ds.data_store import DataStore
    from data_cache import DataCache
    DataStore().init(
        users_df=DataCache.load_users(),
        videos_df=DataCache.load_videos(),
        operations_df=DataCache.load_operations()
    )
    logging.info("自建数据结构层初始化成功")
except Exception as e:
    logging.error(f"自建数据结构初始化失败: {e}")
    if not data_init_error:
        data_init_error = str(e)

# 初始化 Bandit 持久化层
try:
    from ds.bandit_store import BanditStore
    BanditStore().init()
    logging.info("BanditStore 初始化成功")
except Exception as e:
    logging.error(f"BanditStore 初始化失败: {e}")

# ============================================================
# 首页
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/test')
def test_page():
    return render_template('test.html')


# ============================================================
# 健康检查
# ============================================================
@app.route('/api/health')
def health():
    if data_init_error:
        return jsonify({"status": "error", "error": data_init_error}), 503
    return jsonify({"status": "ok", "data_ready": True})


# ============================================================
# 数据统计（供前端中心卡片实时展示）
# ============================================================
@app.route('/api/stats')
def api_stats():
    try:
        from data_cache import DataCache
        videos = DataCache.load_videos()
        users = DataCache.load_users()
        ops = DataCache.load_operations()
        return jsonify({
            "success": True,
            "videos_count": len(videos) if videos is not None else 0,
            "users_count": len(users) if users is not None else 0,
            "operations_count": len(ops) if ops is not None else 0,
            "data_ready": True
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# 图片服务
# ============================================================
@app.route('/api/images/data/<path:filename>')
def serve_data_image(filename):
    path = os.path.join(BASE_DIR, 'data', filename)
    if not os.path.exists(path):
        return jsonify({"error": "Image not found"}), 404
    return send_from_directory(os.path.join(BASE_DIR, 'data'), filename)


@app.route('/api/images/results/<path:filename>')
def serve_results_image(filename):
    path = os.path.join(BASE_DIR, 'results', filename)
    if not os.path.exists(path):
        return jsonify({"error": "Image not found"}), 404
    return send_from_directory(os.path.join(BASE_DIR, 'results'), filename)


# ============================================================
# 数据爬取：从 B站 获取真实数据
# ============================================================
import threading

@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    import crawl_real_data
    # 防止重复触发
    if crawl_real_data.crawl_progress.get("running"):
        return jsonify({"success": False, "error": "抓取正在进行中，请等待完成"}), 409

    def _run():
        try:
            crawl_real_data.crawl_and_save_all()
        except Exception as e:
            logging.error(f"爬取失败: {e}", exc_info=True)
            crawl_real_data._update_progress(running=False, error=str(e))

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"success": True, "message": "抓取已启动"})


@app.route('/api/crawl/progress')
def api_crawl_progress():
    import crawl_real_data
    with crawl_real_data._progress_lock:
        p = dict(crawl_real_data.crawl_progress)
    return jsonify(p)


# ============================================================
# Task 1: 相似用户分析
# ============================================================
@app.route('/api/task1/similar-users', methods=['POST'])
def api_task1():
    try:
        body = request.get_json(silent=True) or {}
        user_id_str = str(body.get('user_id', '')).strip()

        if not user_id_str:
            return jsonify({"success": False, "error": "请输入用户ID"}), 400
        if not user_id_str.isdigit():
            return jsonify({"success": False, "error": "用户ID必须为数字"}), 400

        user_id = int(user_id_str)
        # HashMap O(1) 查询 (替代 pandas O(n) 扫描)
        from ds.data_store import DataStore
        if not DataStore().user_exists(user_id):
            return jsonify({"success": False, "error": "用户ID不存在"}), 400

        import task1_similar_users
        results = task1_similar_users.find_similar_users(user_id)
        data = [
            {"rank": i + 1, "user_ID": row["user_ID"], "similarity": f"{row['similarity']:.4f}"}
            for i, row in enumerate(results)
        ]
        return jsonify({"success": True, "data": data})

    except Exception as e:
        logging.error(f"Task1 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"内部错误: {str(e)}"}), 500


# ============================================================
# Task 2: 视频推荐
# ============================================================
@app.route('/api/task2/recommend-videos', methods=['POST'])
def api_task2():
    try:
        body = request.get_json(silent=True) or {}
        user_id_str = str(body.get('user_id', '')).strip()

        if not user_id_str:
            return jsonify({"success": False, "error": "请输入用户ID"}), 400
        if not user_id_str.isdigit():
            return jsonify({"success": False, "error": "用户ID必须为数字"}), 400

        user_id = int(user_id_str)
        # HashMap O(1) 查询 (替代 pandas O(n) 扫描)
        from ds.data_store import DataStore
        if not DataStore().user_exists(user_id):
            return jsonify({"success": False, "error": "用户ID不存在"}), 400

        use_enhanced = body.get('use_enhanced', False)

        import task2_recommend_videos
        results = task2_recommend_videos.recommend_videos(user_id, use_enhanced=use_enhanced)
        data = [
            {"Video_ID": row["Video_ID"], "label": row["label"],
             "Overall_rating": f"{row['Overall_rating']:.2f}",
             "reason": row.get("reason", ""),
             "enhanced": row.get("enhanced", False),
             "ts_boost": row.get("ts_boost", ""),
             "linucb_boost": row.get("linucb_boost", "")}
            for row in results
        ]
        return jsonify({"success": True, "data": data, "enhanced_mode": use_enhanced})

    except Exception as e:
        logging.error(f"Task2 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"内部错误: {str(e)}"}), 500


# ============================================================
# Task 3: 热度预测
# ============================================================
@app.route('/api/task3/predict-heat', methods=['POST'])
def api_task3():
    try:
        body = request.get_json(silent=True) or {}
        video_id_str = str(body.get('video_id', '')).strip()

        if not video_id_str:
            return jsonify({"success": False, "error": "请输入视频ID"}), 400
        if not video_id_str.isdigit():
            return jsonify({"success": False, "error": "视频ID必须为数字"}), 400

        video_id = int(video_id_str)
        # HashMap O(1) 查询 (替代 pandas O(n) 扫描)
        from ds.data_store import DataStore
        if not DataStore().video_exists(video_id):
            return jsonify({"success": False, "error": "视频ID不存在"}), 400

        from task3_predict_heat import predict_video_heat
        result = predict_video_heat(video_id)

        return jsonify({
            "success": True,
            "history": result["history"],
            "forecast": [round(v, 2) for v in result["forecast"]],
            "forecast_days": result.get("forecast_days", list(range(8, 15))),
            "plot_url": "/api/images/data/heat_plot.png"
        })

    except Exception as e:
        logging.error(f"Task3 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"内部错误: {str(e)}"}), 500


# ============================================================
# Task 4: 用户聚类
# ============================================================
@app.route('/api/task4/user-clustering', methods=['POST'])
def api_task4():
    try:
        body = request.get_json(silent=True) or {}
        n_clusters = int(body.get('n_clusters', 10))

        if n_clusters < 2 or n_clusters > 20:
            return jsonify({"success": False, "error": "聚类数量应在2-20之间"}), 400

        import task4_user_clustering
        result = task4_user_clustering.cluster_users(n_clusters=n_clusters)

        # 同步到 SQLite
        try:
            import pandas as pd
            df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'users_clustered.csv'))
            import database
            database.save_clustered_users(df)
        except Exception:
            pass

        # 用户簇已变更，刷新 BanditStore 中的簇映射和 LinUCB
        try:
            from ds.bandit_store import BanditStore
            BanditStore().reset()
        except Exception:
            pass

        return jsonify({
            "success": True,
            "data": result["data"],
            "plot_url": "/api/images/results/user_clusters.png"
        })

    except Exception as e:
        logging.error(f"Task4 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"内部错误: {str(e)}"}), 500


# ============================================================
# Task 5: 视频聚类
# ============================================================
@app.route('/api/task5/video-clustering', methods=['POST'])
def api_task5():
    try:
        body = request.get_json(silent=True) or {}
        n_clusters = int(body.get('n_clusters', 5))

        if n_clusters < 2 or n_clusters > 20:
            return jsonify({"success": False, "error": "聚类数量应在2-20之间"}), 400

        import task5_video_clustering
        result = task5_video_clustering.cluster_videos(n_clusters=n_clusters)

        # 同步到 SQLite
        try:
            import pandas as pd
            df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'videos_clustered.csv'))
            import database
            database.save_clustered_videos(df)
        except Exception:
            pass

        # 视频簇已变更，刷新 BanditStore 中的簇映射、TS 和 LinUCB
        try:
            from ds.bandit_store import BanditStore
            BanditStore().reset()
        except Exception:
            pass

        return jsonify({
            "success": True,
            "data": result["data"],
            "plot_url": "/api/images/results/video_clusters.png"
        })

    except Exception as e:
        logging.error(f"Task5 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"内部错误: {str(e)}"}), 500


# ============================================================
# Task 6.1: SVD Embedding
# ============================================================
@app.route('/api/task6/embedding', methods=['POST'])
def api_task6_embedding():
    try:
        body = request.get_json(silent=True) or {}
        embedding_dim = int(body.get('embedding_dim', 20))

        if embedding_dim < 10 or embedding_dim > 50:
            return jsonify({"success": False, "error": "Embedding维度应在10-50之间"}), 400

        users_path = os.path.join(BASE_DIR, 'data', 'users_clustered.csv')
        videos_path = os.path.join(BASE_DIR, 'data', 'videos_clustered.csv')
        if not os.path.exists(users_path) or not os.path.exists(videos_path):
            return jsonify({
                "success": False,
                "error": "请先运行用户聚类分析和视频聚类分析（Task 4/5）"
            }), 400

        import Alpha_embedding_Cluster
        t1 = time.time()
        result = Alpha_embedding_Cluster.get_cluster_embeddings(embedding_dim=embedding_dim)
        t2 = time.time()

        if "error" in result:
            return jsonify({"success": False, "error": result["error"]}), 500

        # 重新初始化 LinUCB
        try:
            from ds.bandit_store import BanditStore
            BanditStore().reset()
        except Exception:
            pass

        return jsonify({
            "success": True,
            "message": result.get("message", "Embedding 生成完成"),
            "user_embeddings_shape": str(result.get("user_embeddings_shape", "")),
            "video_embeddings_shape": str(result.get("video_embeddings_shape", "")),
            "runtime": f"{t2 - t1:.2f} s"
        })

    except Exception as e:
        logging.error(f"Task6 Embedding 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"内部错误: {str(e)}"}), 500


# ============================================================
# Task 6.2: Thompson Sampling (持久化 + 真实数据)
# ============================================================
@app.route('/api/task6/thompson-sampling', methods=['POST'])
def api_task6_thompson():
    try:
        from ds.bandit_store import BanditStore
        store = BanditStore()
        store.ensure_init()
        t1 = time.time()

        # 使用真实簇数据进行多轮 TS 训练
        body = request.get_json(silent=True) or {}
        num_rounds = int(body.get('num_rounds', 30))
        num_rounds = min(num_rounds, 100)

        # 随机采样真实用户和视频进行模拟训练
        import random
        all_users = list(store.user_cluster_map.keys())
        all_videos = list(store.video_cluster_map.keys())

        for _ in range(num_rounds):
            uid = random.choice(all_users)
            vid = random.choice(all_videos)
            v_cluster = store.video_cluster_map.get(vid)
            if v_cluster is None:
                continue
            # 模拟反馈: 高CTR簇有更高概率获得正反馈（使用真实 CTR 估计）
            cluster_ctr = store.get_cluster_ctr(v_cluster)
            # 第一次训练时 CTR 接近 0.5 (先验), 随训练逐渐体现真实分布
            liked = random.random() < max(0.15, min(0.85, cluster_ctr + random.uniform(-0.2, 0.2)))
            store.apply_feedback(uid, vid, liked)

        t2 = time.time()

        # 生成可视化
        ts_plot = store.generate_ts_plot()
        ts_ctr_plot = store.generate_ts_ctr_plot()

        # 收集簇状态
        state = store.get_state()

        return jsonify({
            "success": True,
            "message": f"TS 训练完成: {num_rounds} 轮, 覆盖 {len(state['ts_clusters'])} 个簇",
            "rounds": num_rounds,
            "clusters": state['ts_clusters'],
            "ts_plot_url": ts_plot,
            "ts_ctr_plot_url": ts_ctr_plot,
            "runtime": f"{t2 - t1:.2f} s"
        })

    except Exception as e:
        logging.error(f"Task6 TS 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"内部错误: {str(e)}"}), 500


# ============================================================
# Task 6.3: LinUCB (持久化 + 真实数据)
# ============================================================
@app.route('/api/task6/linucb', methods=['POST'])
def api_task6_linucb():
    try:
        from ds.bandit_store import BanditStore
        store = BanditStore()
        store.ensure_init()

        if not store.linucb_ready:
            return jsonify({
                "success": False,
                "error": "请先运行 SVD Embedding（Task 6 第一模块）生成 Embedding 文件"
            }), 400

        body = request.get_json(silent=True) or {}
        num_rounds = int(body.get('num_rounds', 30))
        num_rounds = min(num_rounds, 100)
        t1 = time.time()

        import random
        all_users = list(store.user_cluster_map.keys())
        all_videos = list(store.video_cluster_map.keys())

        for _ in range(num_rounds):
            uid = random.choice(all_users)
            vid = random.choice(all_videos)
            u_cluster = store.user_cluster_map.get(uid)
            v_cluster = store.video_cluster_map.get(vid)
            if u_cluster is None or v_cluster is None:
                continue

            # 获取当前 UCB 比较
            ucb_current = store.linucb_bandit.get_ucb_score(u_cluster, v_cluster)
            # 模拟奖励 (基于真实簇交互可能有不同偏好)
            reward = random.uniform(0, 1)
            store.apply_feedback(uid, vid, reward > 0.5)

        t2 = time.time()

        linucb_plot = store.generate_linucb_plot()
        state = store.get_state()

        return jsonify({
            "success": True,
            "message": f"LinUCB 训练完成: {num_rounds} 轮",
            "rounds": num_rounds,
            "linucb_history": state['linucb_history'],
            "linucb_plot_url": linucb_plot,
            "runtime": f"{t2 - t1:.2f} s"
        })

    except Exception as e:
        logging.error(f"Task6 LinUCB 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"内部错误: {str(e)}"}), 500


# ============================================================
# Task 6.4: 交互式训练 — 获取候选视频
# ============================================================
@app.route('/api/task6/interactive-candidates', methods=['POST'])
def api_task6_candidates():
    try:
        from ds.bandit_store import BanditStore
        store = BanditStore()
        store.ensure_init()

        body = request.get_json(silent=True) or {}
        user_id = body.get('user_id', None)

        result = store.pick_candidates(user_id=user_id, n=4)

        return jsonify({
            "success": True,
            "user_id": result['user_id'],
            "candidates": result['candidates'],
            "round": store.round_count + 1,
            "linucb_ready": store.linucb_ready
        })

    except Exception as e:
        logging.error(f"交互式候选 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Task 6.5: 交互式训练 — 提交反馈
# ============================================================
@app.route('/api/task6/interactive-feedback', methods=['POST'])
def api_task6_feedback():
    try:
        from ds.bandit_store import BanditStore
        store = BanditStore()
        store.ensure_init()

        body = request.get_json(silent=True) or {}
        user_id = int(body.get('user_id', 0))
        video_id = int(body.get('video_id', 0))
        liked = bool(body.get('liked', True))

        if not user_id or not video_id:
            return jsonify({"success": False, "error": "缺少 user_id 或 video_id"}), 400

        store.apply_feedback(user_id, video_id, liked)

        # 生成图表
        ts_plot = store.generate_ts_plot()
        ts_ctr_plot = store.generate_ts_ctr_plot()
        linucb_plot = store.generate_linucb_plot() if store.linucb_ready else None

        state = store.get_state()

        return jsonify({
            "success": True,
            "round": store.round_count,
            "state": state,
            "ts_plot_url": ts_plot,
            "ts_ctr_plot_url": ts_ctr_plot,
            "linucb_plot_url": linucb_plot
        })

    except Exception as e:
        logging.error(f"交互式反馈 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Task 6.6: 获取 Bandit 状态 + 图表
# ============================================================
@app.route('/api/task6/state', methods=['GET'])
def api_task6_state():
    try:
        from ds.bandit_store import BanditStore
        store = BanditStore()
        store.ensure_init()

        state = store.get_state()
        ts_plot = store.generate_ts_plot()
        ts_ctr_plot = store.generate_ts_ctr_plot()
        linucb_plot = store.generate_linucb_plot() if store.linucb_ready else None

        return jsonify({
            "success": True,
            "state": state,
            "ts_plot_url": ts_plot,
            "ts_ctr_plot_url": ts_ctr_plot,
            "linucb_plot_url": linucb_plot
        })

    except Exception as e:
        logging.error(f"Bandit 状态 错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Task 6.7: 重置 Bandit
# ============================================================
@app.route('/api/task6/reset', methods=['POST'])
def api_task6_reset():
    try:
        from ds.bandit_store import BanditStore
        BanditStore().reset()
        return jsonify({"success": True, "message": "Bandit 状态已重置"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Feature B: 热门视频排行榜 (MaxHeap Top-K)
# ============================================================
@app.route('/api/top-videos')
def api_top_videos():
    try:
        sort_by = request.args.get('sort', 'views')
        from ds.data_store import DataStore
        from ds.max_heap import MaxHeap

        store = DataStore()
        heap = MaxHeap()

        if sort_by == 'likes':
            # 按点赞数
            for vid in store.videos_map.keys():
                v = store.videos_map.get(vid)
                if v:
                    heap.push(v['likes'], vid)
        elif sort_by == 'ratio':
            # 按点赞率 (最低1000观看量门槛, 避免小样本偏差)
            MIN_VIEWS = 1000
            for vid in store.videos_map.keys():
                v = store.videos_map.get(vid)
                if v and v['views'] >= MIN_VIEWS:
                    rate = v['likes'] / v['views']
                    heap.push(rate, vid)
        else:
            # 默认按观看量
            for vid in store.videos_map.keys():
                v = store.videos_map.get(vid)
                if v:
                    heap.push(v['views'], vid)

        top = heap.top_k(10)
        data = []
        for i, (score, vid) in enumerate(top):
            v = store.videos_map.get(vid)
            data.append({
                "rank": i + 1,
                "Video_ID": int(vid),
                "tag": v['tag'] if v else '未知',
                "views": v['views'] if v else 0,
                "likes": v['likes'] if v else 0,
                "score": int(score)
            })

        return jsonify({"success": True, "data": data, "sort_by": sort_by})
    except Exception as e:
        logging.error(f"排行榜错误: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# 启动
# ============================================================
if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  Just One More - Web 版本")
    print("  访问地址: http://localhost:8080")
    print("=" * 50 + "\n")
    app.run(host='0.0.0.0', port=8080, debug=True)
