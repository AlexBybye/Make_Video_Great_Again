# -*- coding: utf-8 -*-
import pandas as pd
import random
import numpy as np
import logging
import os
import requests
import time
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- 您提供的验证函数和权重生成函数 ---

def validate_user_data(df: pd.DataFrame) -> bool:
    """验证用户数据的有效性"""
    try:
        # 检查必要的列是否存在
        if not all(col in df.columns for col in ['id', 'age']):
            logging.error("用户数据缺少必要的列")
            return False

        # 检查数据类型
        # 注意: B站视频ID可能超出int32范围，但用户ID和年龄一般在int64内
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
        # video_id 使用 object 或 string 兼容 B 站的 BV 号
        # 但由于排行榜接口返回的是 aid (数字ID)，这里仍假设为 int64
        if not all(df[col].dtype == 'int64' for col in ['user_id', 'video_id', 'day']):
            logging.error("用户ID、视频ID和天数必须是整数类型 (或确保 video_id 可转为 int64)")
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


# --- Bilibili 爬虫和生成逻辑 ---

# B站全站日排行榜 API 接口 (返回 JSON 数据)
BILIBILI_RANK_API = "https://api.bilibili.com/x/web-interface/ranking/v2"
HEADERS = {
    # 模拟浏览器访问，非常重要
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.bilibili.com/ranking/'
}

# --- 模拟参数 (保持与您原代码一致，以便快速测试) ---
SIMULATED_USERS = 10000
MIN_OPS_PER_USER = 75
MAX_OPS_PER_USER = 125
MAX_VIDEOS_TO_FETCH = 500


def fetch_bilibili_ranking(max_results: int) -> pd.DataFrame:
    """
    抓取 B站全站排行榜的视频数据。
    """
    logging.info("开始通过 Bilibili API 抓取热门视频数据...")

    video_list = []
    page = 1

    while len(video_list) < max_results:
        params = {
            'rid': 0,  # 0 代表全部分区
            'type': 'all',  # 排行榜类型
            'day': 3,  # 3天内热门
            'pn': page  # 页码
        }

        try:
            response = requests.get(BILIBILI_RANK_API, headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['code'] != 0 or not data['data'].get('list'):
                logging.warning("API 响应异常或无数据，停止抓取。")
                break

            items = data['data']['list']
            if not items:
                break

            for item in items:
                if len(video_list) >= max_results:
                    break

                # 提取视频信息，B站 aid 是数字ID，可转换为 int64
                stats = item.get('stat', {})
                video_list.append({
                    'video_id': item.get('aid'),  # B站的视频ID (数字)
                    'views': stats.get('view', 0),
                    'likes': stats.get('like', 0)
                })

            page += 1
            time.sleep(1)  # 增加延迟，防止触发反爬

        except requests.exceptions.RequestException as e:
            logging.error(f"Bilibili API 请求失败: {e}")
            break
        except Exception as e:
            logging.error(f"数据解析或处理失败: {e}")
            break

    df = pd.DataFrame(video_list)

    # 确保 video_id 是 int64 类型
    if 'video_id' in df.columns:
        df['video_id'] = pd.to_numeric(df['video_id'], errors='coerce').fillna(0).astype('int64')

    logging.info(f"成功抓取 {len(df)} 条 B站视频记录")
    return df


def generate_users_and_operations(videos_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    基于爬取的 B站视频数据，生成模拟的用户和操作数据。
    """

    # --- 1. 模拟生成用户数据 (users.csv) ---
    logging.info(f"模拟生成 {SIMULATED_USERS} 个用户")
    ages = np.random.normal(loc=35, scale=10, size=SIMULATED_USERS)
    ages = np.clip(ages, 18, 60).astype(int)

    users_df = pd.DataFrame({
        'id': range(1, SIMULATED_USERS + 1),
        'age': ages
    }).astype({'id': 'int64', 'age': 'int64'})

    # --- 2. 模拟生成操作数据 (operations.csv) ---
    logging.info("开始模拟生成用户操作记录")
    operations = []

    # 使用真实的 B站视频 ID
    video_ids = videos_df['video_id'].tolist()

    # 移除 ID 为 0 的错误或缺失数据
    video_ids = [vid for vid in video_ids if vid > 0]

    if not video_ids:
        logging.error("没有有效的视频 ID 来生成操作数据。")
        return users_df, pd.DataFrame(columns=['user_id', 'video_id', 'liked', 'day'])

    for user_id in users_df['id']:
        num_ops = random.randint(MIN_OPS_PER_USER, MAX_OPS_PER_USER)
        days = generate_days(num_ops)

        for day in days:
            # 随机选择用户观看的 B站视频
            video_id = random.choice(video_ids)

            # 模拟点赞逻辑: 30% 概率点赞 (复用您的原逻辑)
            liked = 1 if random.random() < 0.3 else 0

            operations.append({
                'user_id': user_id,
                'video_id': video_id,
                'liked': liked,
                'day': day
            })

    operations_df = pd.DataFrame(operations).astype({
        'user_id': 'int64',
        'video_id': 'int64',
        'liked': 'int64',
        'day': 'int64'
    })

    return users_df, operations_df


def crawl_and_save_bilibili_data():
    """执行完整的抓取、模拟、验证和保存流程"""
    try:
        # 1. 抓取 B站公开视频数据
        videos_df = fetch_bilibili_ranking(MAX_VIDEOS_TO_FETCH)

        if videos_df.empty or videos_df['video_id'].nunique() < 10:
            logging.error("未能抓取到足够多的有效视频数据，终止流程。")
            return

        # 2. 基于视频数据，模拟生成用户和操作数据
        users_df, operations_df = generate_users_and_operations(videos_df)

        # 3. 验证数据
        if not validate_user_data(users_df):
            raise ValueError("模拟的用户数据验证失败")

        if not validate_operations_data(operations_df):
            raise ValueError("模拟的操作数据验证失败")

        # 4. 保存数据
        os.makedirs('data', exist_ok=True)
        users_df.to_csv('data/users.csv', index=False, mode='w')
        operations_df.to_csv('data/operations.csv', index=False, mode='w')

        # (可选) 保存抓取到的视频信息
        videos_df.to_csv('data/bilibili_user_operation.csv', index=False, mode='w')

        logging.info("--- Bilibili 数据抓取、模拟和保存成功完成 ---")
        logging.info(f"抓取的 B站视频数量: {len(videos_df)}")
        logging.info(f"保存的用户记录数: {len(users_df)}")
        logging.info(f"保存的操作记录数: {len(operations_df)}")

    except Exception as e:
        logging.error(f"Bilibili 数据获取和保存失败: {str(e)}")


if __name__ == '__main__':
    crawl_and_save_bilibili_data()