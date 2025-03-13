# -*- coding: utf-8 -*-
import pandas as pd
import random
import numpy as np
from generate_videos import generate_videos

def generate_day_weights():
    # 生成七天的权重，每个权重不低于0.1且不高于0.4
    weights = np.random.uniform(0.1, 0.4, 7)
    weights /= weights.sum()  # 归一化确保总和为1
    return weights

def generate_days(num_ops):
    # 根据随机生成的权重分配天数
    weights = generate_day_weights()
    
    # 根据权重生成天数序列
    days = np.random.choice(np.arange(1, 8), num_ops, p=weights)
    
    # 按时间顺序排列
    days = np.sort(days)
    
    return days.tolist()

def generate_users_operations():
    # 配置参数
    num_users = 10_000
    num_videos = 100_000
    min_ops, max_ops = 100, 200
    
    # 初始化用户年龄，采用正态分布更符合实际情况
    ages = np.random.normal(loc=35, scale=10, size=num_users)  # 均值35，标准差10
    ages = np.clip(ages, 18, 60).astype(int)  # 限制年龄范围在18-60岁
    
    users = pd.DataFrame({
        'id': range(1, num_users + 1),
        'age': ages
    })
    
    # 初始化视频统计信息（用NumPy加速）
    views = np.zeros(num_videos, dtype=int)
    likes = np.zeros(num_videos, dtype=int)
    
    # 读取视频数据
    videos = pd.read_csv('videos.csv')
    viewed_by = videos['viewed_by'].apply(eval).tolist()  # 将字符串转换为列表
    liked_by = videos['liked_by'].apply(eval).tolist()  # 将字符串转换为列表
    
    # 生成操作记录
    operations = []
    for user_id in users['id']:
        num_ops = random.randint(min_ops, max_ops)
        days = generate_days(num_ops)
        
        for day in days:
            video_id = random.randint(1, num_videos)
            video_idx = video_id - 1
            
            # 更新浏览和点赞
            views[video_idx] += 1
            if random.random() < 0.3:  # 30%概率点赞
                likes[video_idx] += 1
                liked = 1
                # 记录点赞用户和日期
                liked_by[video_idx].append((user_id, day))
            else:
                liked = 0
            
            # 记录操作（添加day字段）
            operations.append({
                'user_id': user_id,
                'video_id': video_id,
                'liked': liked,
                'day': day
            })
            
            # 记录观看用户和日期
            viewed_by[video_idx].append((user_id, day))
    
    # 保存用户信息
    users.to_csv('users.csv', index=False)
    
    # 保存操作记录
    pd.DataFrame(operations).to_csv('operations.csv', index=False)
    
    # 更新视频统计信息并保存
    videos['views'] = views
    videos['likes'] = likes
    videos['viewed_by'] = viewed_by
    videos['liked_by'] = liked_by
    videos.to_csv('videos.csv', index=False)

