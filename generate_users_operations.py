# -*- coding: utf-8 -*-
import pandas as pd
import random
import numpy as np
import logging
import os
from typing import List, Dict, Any
from generate_videos import generate_videos

def validate_user_data(df: pd.DataFrame) -> bool:
    """验证用户数据的有效性"""
    try:
        # 检查必要的列是否存在
        if not all(col in df.columns for col in ['id', 'age']):
            logging.error("用户数据缺少必要的列")
            return False

        # 检查数据类型
        if not df['id'].dtype == 'int64' or not df['age'].dtype == 'int64':
            logging.error("用户ID和年龄必须是整数类型")
            return False

        # 检查数据完整性
        if df['id'].isnull().any() or df['age'].isnull().any():
            logging.error("用户数据存在空值")
            return False

        # 检查年龄范围
        if (df['age'] < 18).any() or (df['age'] > 60).any():
            logging.error("用户年龄必须在18-60岁之间")
            return False

        return True
    except Exception as e:
        logging.error(f"用户数据验证失败: {str(e)}")
        return False

def validate_operations_data(df: pd.DataFrame) -> bool:
    """验证操作数据的有效性"""
    try:
        # 检查必要的列是否存在
        required_columns = ['user_id', 'video_id', 'liked', 'day']
        if not all(col in df.columns for col in required_columns):
            logging.error("操作数据缺少必要的列")
            return False

        # 检查数据类型
        if not all(df[col].dtype == 'int64' for col in ['user_id', 'video_id', 'day']):
            logging.error("用户ID、视频ID和天数必须是整数类型")
            return False

        # 检查数据完整性
        if df[required_columns].isnull().any().any():
            logging.error("操作数据存在空值")
            return False

        # 检查数值范围
        if (df['day'] < 1).any() or (df['day'] > 7).any():
            logging.error("天数必须在1-7之间")
            return False

        if not df['liked'].isin([0, 1]).all():
            logging.error("点赞标记必须是0或1")
            return False

        return True
    except Exception as e:
        logging.error(f"操作数据验证失败: {str(e)}")
        return False

def generate_day_weights() -> np.ndarray:
    """生成每日权重"""
    weights = np.random.uniform(0.1, 0.4, 7)
    return weights / weights.sum()

def generate_days(num_ops: int) -> List[int]:
    """生成操作天数"""
    weights = generate_day_weights()
    days = np.random.choice(np.arange(1, 8), num_ops, p=weights)
    return np.sort(days).tolist()

def generate_users_operations(force: bool = False) -> None:
    """
    生成用户操作数据
    Args:
        force: 是否强制重新生成数据
    """
    try:
        # 检查是否需要生成数据
        if not force and os.path.exists('data/users.csv') and os.path.exists('data/operations.csv'):
            users_df = pd.read_csv('data/users.csv')
            ops_df = pd.read_csv('data/operations.csv')
            if validate_user_data(users_df) and validate_operations_data(ops_df):
                logging.info("使用现有用户和操作数据")
                return

        logging.info("开始生成新的用户和操作数据")
        
        # 设置参数
        num_users = 50000
        num_videos = 500000
        min_ops, max_ops = 800, 1200
        
        # 生成用户年龄（使用NumPy优化性能）
        ages = np.random.normal(loc=35, scale=10, size=num_users)
        ages = np.clip(ages, 18, 60).astype(int)
        
        # 创建用户数据
        users_df = pd.DataFrame({
            'id': range(1, num_users + 1),
            'age': ages
        })

        # 初始化视频统计信息
        views = np.zeros(num_videos, dtype=int)
        likes = np.zeros(num_videos, dtype=int)
        
        # 读取视频数据
        videos_df = pd.read_csv('data/videos.csv')
        viewed_by = videos_df['viewed_by'].apply(eval).tolist()
        liked_by = videos_df['liked_by'].apply(eval).tolist()
        
        # 生成操作记录
        operations = []
        for user_id in users_df['id']:
            num_ops = random.randint(min_ops, max_ops)
            days = generate_days(num_ops)
            
            for day in days:
                video_id = random.randint(1, num_videos)
                video_idx = video_id - 1
                
                # 更新统计信息
                views[video_idx] += 1
                if random.random() < 0.3:  # 30%概率点赞
                    likes[video_idx] += 1
                    liked = 1
                    liked_by[video_idx].append((user_id, day))
                else:
                    liked = 0
                
                # 记录操作
                operations.append({
                    'user_id': user_id,
                    'video_id': video_id,
                    'liked': liked,
                    'day': day
                })
                
                # 记录观看用户
                viewed_by[video_idx].append((user_id, day))
        
        # 创建操作数据
        operations_df = pd.DataFrame(operations)
        
        # 验证数据
        if not validate_user_data(users_df):
            raise ValueError("生成的用户数据验证失败")
        if not validate_operations_data(operations_df):
            raise ValueError("生成的操作数据验证失败")
        
        # 保存数据
        os.makedirs('data', exist_ok=True)
        users_df.to_csv('data/users.csv', index=False, mode='w')
        operations_df.to_csv('data/operations.csv', index=False, mode='w')
        
        # 更新视频数据
        videos_df['views'] = views
        videos_df['likes'] = likes
        videos_df['viewed_by'] = viewed_by
        videos_df['liked_by'] = liked_by
        videos_df.to_csv('data/videos.csv', index=False, mode='w')
        
        logging.info("用户和操作数据生成完成")

    except Exception as e:
        logging.error(f"生成用户和操作数据失败: {str(e)}")
        raise
