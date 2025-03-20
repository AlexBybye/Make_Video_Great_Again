# -*- coding: utf-8 -*-
import pandas as pd
import random

def generate_videos():
    tags = ['movie', 'music', 'game', 'life', 'tech', 'fashion', 'sports', 'food', 'education', 'travel']
    num_videos = 100_000
    
    # 生成视频列表（仅标签）
    video_tags = [random.choice(tags) for _ in range(num_videos)]
    
    # 初始化每条视频的观看记录和点赞记录（用户ID和日期）
    viewed_by = [[] for _ in range(num_videos)]
    liked_by = [[] for _ in range(num_videos)]
    
    # 保存到DataFrame
    df = pd.DataFrame({
        'id': range(1, num_videos + 1),
        'tag': video_tags,
        'views': 0,  # 初始值，后续通过操作记录更新
        'likes': 0,
        'viewed_by': viewed_by,  # 记录每条视频在哪天被哪些用户观看
        'liked_by': liked_by  # 记录每条视频在哪天被哪些用户点赞
    })
    df.to_csv('data/videos.csv', index=False)

