import random
import pandas as pd
from video import Video
from user import User
from scipy.sparse import csr_matrix  # 确保导入 csr_matrix
import numpy as np

# 定义视频分类标签
CATEGORIES = ["music", "sports", "gaming", "comedy", "education", "lifestyle"]

def generate_videos(num_videos):
    """生成视频数据"""
    return [Video(f"video_{i}", random.choice(CATEGORIES)) for i in range(num_videos)]

def generate_users(num_users):
    """生成用户数据"""
    return [User(f"user_{i}", random.choice(["male", "female"]), random.randint(18, 65)) for i in range(num_users)]

def simulate_user_behavior(users, videos, num_interactions):
    """模拟用户行为并返回用户-视频交互矩阵"""
    rows, cols, data = [], [], []
    user_id_to_row = {user.uid: i for i, user in enumerate(users)}
    video_id_to_col = {video.video_id: i for i, video in enumerate(videos)}

    for _ in range(num_interactions):
        user = random.choice(users)
        video = random.choice(videos)
        date = random.randint(0, 4)  # 随机选择一天（0-4）
        action = random.choice(["like", "comment", "share"])
        # 根据 action 的值更新视频的行为数据
        if action == "like":
            video.like(date)
            weight = 1
        elif action == "comment":
            video.comment(date)
            weight = 2
        elif action == "share":
            video.share(date)
            weight = 3

        # 记录交互数据
        rows.append(user_id_to_row[user.uid])
        cols.append(video_id_to_col[video.video_id])
        data.append(weight)

    # 返回稀疏矩阵
    return csr_matrix((data, (rows, cols)), shape=(len(users), len(videos)))

def save_videos_to_csv(videos, filename="videos.csv"):
    """将视频数据保存为 CSV 文件"""
    video_data = [video.get_stats() for video in videos]
    df = pd.DataFrame(video_data)
    df.to_csv(filename, index=False)

def save_users_to_csv(users, filename="users.csv"):
    """将用户数据保存为 CSV 文件"""
    user_data = [{"uid": user.uid, "gender": user.gender, "age": user.age} for user in users]
    df = pd.DataFrame(user_data)
    df.to_csv(filename, index=False)

if __name__ == "__main__":
    num_videos = 100000  # 10 万视频
    num_users = 10000    # 1 万用户
    num_interactions = 4000000  # 400 万次交互

    videos = generate_videos(num_videos)
    users = generate_users(num_users)
    user_video_matrix = simulate_user_behavior(users, videos, num_interactions)

    # 保存数据为 CSV 文件
    save_videos_to_csv(videos, "videos.csv")
    save_users_to_csv(users, "users.csv")