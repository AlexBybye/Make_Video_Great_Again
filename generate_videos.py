# -*- coding: utf-8 -*-
import pandas as pd
import random
import logging
import os
from typing import List, Dict, Any
import numpy as np

def validate_video_data(df: pd.DataFrame) -> bool:
    """验证视频数据的有效性"""
    try:
        # 检查必要的列是否存在
        required_columns = ['id', 'tag', 'views', 'likes', 'viewed_by', 'liked_by']
        if not all(col in df.columns for col in required_columns):
            logging.error("视频数据缺少必要的列")
            return False

        # 检查数据类型
        if not df['id'].dtype == 'int64':
            logging.error("视频ID必须是整数类型")
            return False

        # 检查数据完整性
        if df['id'].isnull().any() or df['tag'].isnull().any():
            logging.error("视频数据存在空值")
            return False

        # 检查数值范围
        if (df['views'] < 0).any() or (df['likes'] < 0).any():
            logging.error("观看数和点赞数不能为负数")
            return False

        return True
    except Exception as e:
        logging.error(f"数据验证失败: {str(e)}")
        return False

def generate_videos(force: bool = False) -> None:
    """
    生成视频数据
    Args:
        force: 是否强制重新生成数据
    """
    try:
        # 检查是否需要生成数据
        if not force and os.path.exists('data/videos.csv'):
            df = pd.read_csv('data/videos.csv')
            if validate_video_data(df):
                logging.info("使用现有视频数据")
                return

        logging.info("开始生成新的视频数据")
        
        # 视频标签列表
        tags = ['movie', 'music', 'game', 'life', 'tech', 'fashion', 'sports', 'food', 'education', 'travel']
        num_videos = 500000
        
        # 使用列表推导式优化性能
        video_tags = [random.choice(tags) for _ in range(num_videos)]
        
        # 使用NumPy数组优化性能
        views = np.zeros(num_videos, dtype=int)
        likes = np.zeros(num_videos, dtype=int)
        
        # 初始化空列表
        viewed_by = [[] for _ in range(num_videos)]
        liked_by = [[] for _ in range(num_videos)]
        
        # 创建DataFrame
        df = pd.DataFrame({
            'id': range(1, num_videos + 1),
            'tag': video_tags,
            'views': views,
            'likes': likes,
            'viewed_by': viewed_by,
            'liked_by': liked_by
        })

        # 验证数据
        if not validate_video_data(df):
            raise ValueError("生成的视频数据验证失败")

        # 保存数据
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/videos.csv', index=False, mode='w')
        logging.info("视频数据生成完成")

    except Exception as e:
        logging.error(f"生成视频数据失败: {str(e)}")
        raise

