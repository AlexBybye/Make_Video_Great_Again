from simulate_data import generate_videos, generate_users, simulate_user_behavior
from recommend import Recommender
from predict import VideoHeatPredictor
from cluster import VideoCluster, UserCluster
import time

def main():
    # 生成数据
    t1 = time.time()
    num_videos = 100000
    num_users = 10000
    num_interactions = 4000000
    t2 = time.time()
    print(f"初始化耗时: {t2 - t1:.4f} 秒")
    videos = generate_videos(num_videos)
    users = generate_users(num_users)
    user_video_matrix = simulate_user_behavior(users, videos, num_interactions)
    t3 = time.time()
    print(f"模拟耗时: {t3 - t2:.4f} 秒")

    # 初始化推荐系统
    recommender = Recommender(users, videos, user_video_matrix)

    # 示例：为用户 user_0 推荐
    print(f"输入目标用户:(user_123)")
    target_uid = input()
    similar_users = recommender.find_similar_users(target_uid, top_n=5)
    recommended_videos = recommender.recommend_videos(target_uid, top_n=5)

    print(f"相似用户: {similar_users}")
    print(f"推荐视频: {recommended_videos}")
    t4 = time.time()
    print(f"推荐耗时: {t4 - t3:.4f} 秒")

    # 初始化热度预测器
    heat_predictor = VideoHeatPredictor(videos)

    # 示例：预测视频 video_0 的未来热度
    print(f"输入目标视频:(video_123)")
    target_video_id = input()
    future_heat = heat_predictor.predict_heat(target_video_id, future_days=7)
    print(f"视频 {target_video_id} 未来 7 天的热度预测: {future_heat}")

    t5 = time.time()
    print(f"预测耗时: {t5 - t4:.4f} 秒")

    # 初始化聚类分析
    video_cluster = VideoCluster(users, videos, user_video_matrix)
    user_cluster = UserCluster(users, videos, user_video_matrix)

    # 对视频进行聚类
    video_labels, video_user_matrix_reduced = video_cluster.cluster_videos(n_clusters=3)
    print(f"视频聚类标签: {video_labels}")
    video_cluster.plot_video_clusters(video_labels, video_user_matrix_reduced)

    # 对用户进行聚类
    user_labels, user_video_matrix_reduced = user_cluster.cluster_users(n_clusters=3)
    print(f"用户聚类标签: {user_labels}")
    user_cluster.plot_user_clusters(user_labels, user_video_matrix_reduced)

    t6 = time.time()
    print(f"聚类耗时: {t6 - t5:.4f} 秒")

if __name__ == "__main__":
    main()