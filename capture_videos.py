# -*- coding: utf-8 -*-
import pandas as pd
import logging
import os
import requests
import time
from typing import List, Dict, Any
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- 您提供的验证函数 ---

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

        # 检查数据完整性 (这里只检查 ID 和 Tag，因为 views, likes 是数值，viewed_by/liked_by 是列表)
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


# --- Bilibili 抓取逻辑 ---

# B站全站排行榜 API 接口
BILIBILI_RANK_API = "https://api.bilibili.com/x/web-interface/ranking/v2"
# B站分区映射 (RID: Tag名称)
BILI_TAG_MAP = {
    1: '动画', 168: '国创', 3: '音乐', 129: '舞蹈', 4: '游戏', 17: '单机游戏', 36: '科技',
    188: '数码', 160: '生活', 211: '美食', 217: '动物圈', 21: '运动', 76: '鬼畜', 75: '放映厅',
    155: '时尚', 119: '娱乐', 202: '知识', 228: '汽车', 223: '资讯', 16: '影视', 138: '纪录片'
    # 包含了您原始列表 tags 的大部分概念
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.bilibili.com/ranking/'
}
MAX_PAGES_TO_FETCH = 10  # 抓取页数，每页约20条数据


def fetch_bilibili_videos() -> pd.DataFrame:
    """
    抓取 B站多个分区的排行榜数据，并格式化为目标结构。
    """
    logging.info("开始通过 Bilibili API 抓取视频数据...")

    video_list = []

    # 遍历主要分区进行抓取
    for rid, tag_name in BILI_TAG_MAP.items():
        logging.info(f"--- 抓取分区: {tag_name} (RID: {rid}) ---")

        # 抓取前 MAX_PAGES_TO_FETCH 页的数据
        for page in range(1, MAX_PAGES_TO_FETCH + 1):
            params = {
                'rid': rid,  # 分区 ID
                'type': 'all',
                'day': 3,  # 3天内热门
                'pn': page  # 页码
            }

            try:
                response = requests.get(BILIBILI_RANK_API, headers=HEADERS, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data['code'] != 0 or not data['data'].get('list'):
                    logging.info(f"分区 {tag_name} 在第 {page} 页无数据或API响应结束。")
                    break

                items = data['data']['list']
                for item in items:
                    stats = item.get('stat', {})

                    # 抓取核心数据
                    video_list.append({
                        'id': item.get('aid'),  # 视频 ID (数字)
                        'tag': tag_name,  # 分区标签
                        'views': stats.get('view', 0),  # 播放量
                        'likes': stats.get('like', 0),  # 点赞数
                        'viewed_by': '[]',  # 初始化为空列表字符串
                        'liked_by': '[]'  # 初始化为空列表字符串
                    })

                time.sleep(0.5)  # 增加延迟

            except requests.exceptions.RequestException as e:
                logging.error(f"分区 {tag_name} 请求失败: {e}")
                break
            except Exception as e:
                logging.error(f"分区 {tag_name} 数据解析失败: {e}")
                break

    df = pd.DataFrame(video_list).drop_duplicates(subset=['id'])  # 去重

    # 确保 id, views, likes 是 int64 类型
    df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype('int64')
    df['views'] = pd.to_numeric(df['views'], errors='coerce').fillna(0).astype('int64')
    df['likes'] = pd.to_numeric(df['likes'], errors='coerce').fillna(0).astype('int64')

    logging.info(f"最终抓取到 {len(df)} 条不重复的 B站视频记录")
    return df


def crawl_and_save_video_data() -> None:
    """执行抓取、验证和保存的完整流程"""
    try:
        # 1. 抓取视频数据
        videos_df = fetch_bilibili_videos()

        if videos_df.empty:
            logging.error("未能抓取到任何视频数据，终止流程。")
            return

        # 2. 验证数据
        if not validate_video_data(videos_df):
            raise ValueError("抓取并格式化后的视频数据验证失败")

        # 3. 保存数据
        os.makedirs('data', exist_ok=True)
        videos_df.to_csv('data/bilibili_videos.csv', index=False, mode='w')

        logging.info("--- Bilibili 视频数据抓取、验证和保存成功完成 ---")
        logging.info(f"保存的视频记录数: {len(videos_df)}")

    except Exception as e:
        logging.error(f"Bilibili 视频数据获取和保存失败: {str(e)}")
        raise


if __name__ == '__main__':
    crawl_and_save_video_data()