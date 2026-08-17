# -*- coding: utf-8 -*-
import pandas as pd
import logging
import os
import requests
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
}

# B站所有可用分区 RID (104个已验证)
REGION_RIDS = [
    1, 3, 4, 5, 11, 13, 17, 19, 23, 25, 28, 30, 31, 33, 36, 37, 47,
    51, 65, 71, 85, 86, 95, 119, 122, 124, 129, 130, 136, 137, 138,
    145, 147, 152, 153, 155, 156, 160, 161, 162, 164, 167, 168, 172,
    173, 174, 176, 177, 181, 182, 183, 184, 185, 187, 188, 193, 195,
    198, 200, 201, 202, 203, 205, 207, 208, 209, 210, 211, 212, 213,
    214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 227, 228, 229,
    230, 231, 232, 233, 234, 235, 236, 238, 239, 240, 241, 242, 243,
    244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256,
    257, 259, 260
]

# 搜索关键词（作为补充）
SEARCH_KEYWORDS = ['搞笑', '美食', '游戏', '音乐', '科技', '生活', '影视', '知识', '运动', '动物']

POPULAR_API = "https://api.bilibili.com/x/web-interface/popular"
REGION_API = "https://api.bilibili.com/x/web-interface/dynamic/region"
SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"

DELAY = 0.5


def validate_video_data(df: pd.DataFrame) -> bool:
    try:
        required_columns = ['id', 'tag', 'views', 'likes', 'viewed_by', 'liked_by']
        if not all(col in df.columns for col in required_columns):
            return False
        if df['id'].isnull().any() or df['tag'].isnull().any():
            return False
        if (df['views'] < 0).any() or (df['likes'] < 0).any():
            return False
        return True
    except Exception:
        return False


def _add_video(video_list, vid, tag, views, likes):
    video_list.append({
        'id': int(vid), 'tag': str(tag), 'views': int(views or 0),
        'likes': int(likes or 0), 'viewed_by': '[]', 'liked_by': '[]'
    })


def _fetch_popular(progress_callback=None, offset=0.0, weight=0.06) -> list:
    """热门视频 — 约占6%"""
    results = []
    for page in range(1, 15):
        try:
            resp = requests.get(POPULAR_API, headers=HEADERS,
                                params={'pn': page, 'ps': 50}, timeout=10)
            data = resp.json()
            if data['code'] != 0 or not data['data'].get('list'):
                break
            for item in data['data']['list']:
                s = item.get('stat', {})
                _add_video(results, item['aid'], item.get('tname', '其他'), s.get('view', 0), s.get('like', 0))
            if progress_callback:
                progress_callback(offset + weight * page / 15,
                                  f"热门第{page}页 — {len(results)}条", len(results))
            time.sleep(DELAY)
        except Exception as e:
            logging.warning(f"热门抓取中断: {e}")
            break
    return results


def _fetch_one_region(rid, max_pages):
    """抓取单个分区（供并发调用）"""
    items = []
    for page in range(1, max_pages + 1):
        try:
            resp = requests.get(REGION_API, headers=HEADERS,
                                params={'rid': rid, 'pn': page, 'ps': 50}, timeout=10)
            data = resp.json()
            if data['code'] != 0:
                break
            archives = data['data'].get('archives', [])
            if not archives:
                break
            for item in archives:
                items.append({
                    'id': int(item['aid']),
                    'tag': str(item.get('tname', '其他')),
                    'views': int(item['stat']['view']),
                    'likes': int(item['stat']['like']),
                    'viewed_by': '[]',
                    'liked_by': '[]'
                })
            time.sleep(0.08)  # 并发下小延迟
        except Exception:
            break
    return items


def _fetch_regions(progress_callback=None, offset=0.05, weight=0.80) -> list:
    """各分区动态 — 8线程并发，大幅提速"""
    results = []
    total = len(REGION_RIDS)
    done = 0

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {}
        for i, rid in enumerate(REGION_RIDS):
            max_pages = 4 if i < 20 else 2
            futures[pool.submit(_fetch_one_region, rid, max_pages)] = rid

        for fut in as_completed(futures):
            done += 1
            region_items = fut.result()
            results.extend(region_items)
            if progress_callback and done % 5 == 0:
                pct = offset + weight * done / total
                progress_callback(pct, f"分区抓取 {done}/{total} — {len(results)}条", len(results))

    return results


def _fetch_search(progress_callback=None, offset=0.85, weight=0.12) -> list:
    """关键词搜索 — 辅助补充"""
    results = []
    total_kw = len(SEARCH_KEYWORDS)
    for i, kw in enumerate(SEARCH_KEYWORDS):
        kw_count = 0
        for page in range(1, 11):  # 每个关键词取10页
            try:
                resp = requests.get(SEARCH_API, headers=HEADERS,
                                    params={'search_type': 'video', 'keyword': kw,
                                            'page': page}, timeout=10)
                data = resp.json()
                if data['code'] != 0:
                    break
                items = data['data'].get('result', [])
                if not items:
                    break
                for item in items:
                    tag = item.get('typename', '') or (item.get('tag', '').split(',')[0] if item.get('tag') else '其他')
                    _add_video(results, item['aid'], tag, item.get('play', 0), item.get('like', 0))
                    kw_count += 1
                time.sleep(DELAY * 1.5)
            except Exception:
                break
        if progress_callback:
            pct = offset + weight * (i + 1) / total_kw
            progress_callback(pct, f"搜索'{kw}'(+{kw_count}) — 共{len(results)}条", len(results))
    return results


def fetch_bilibili_videos(progress_callback=None) -> pd.DataFrame:
    """
    多源抓取 B站真实视频数据：
    1. 热门接口 (popular)
    2. 分区动态接口 (region) — 主力，104个分区
    3. 搜索接口 (search) — 辅助补充
    合并去重 → 目标 5000+ 真实视频
    """
    logging.info("开始多源抓取 B站视频数据...")

    all_videos = []

    # 包装 progress_callback，统一报告总数
    def _report(pct, detail, _count=0):
        if progress_callback:
            progress_callback(pct, detail, len(all_videos))

    # 第1路：热门
    logging.info("[1/3] 抓取热门视频...")
    all_videos.extend(_fetch_popular(progress_callback=_report, offset=0.0, weight=0.04))

    # 第2路：分区
    logging.info(f"[2/3] 抓取 {len(REGION_RIDS)} 个分区...")
    all_videos.extend(_fetch_regions(progress_callback=_report, offset=0.04, weight=0.78))

    # 第3路：搜索
    logging.info(f"[3/3] {len(SEARCH_KEYWORDS)} 个关键词搜索...")
    all_videos.extend(_fetch_search(progress_callback=_report, offset=0.82, weight=0.14))

    if not all_videos:
        logging.warning("未抓取到任何视频数据")
        return pd.DataFrame(columns=['id', 'tag', 'views', 'likes', 'viewed_by', 'liked_by'])

    if progress_callback:
        progress_callback(0.97, f"去重中 — 原始{len(all_videos)}条", len(all_videos))

    df = pd.DataFrame(all_videos).drop_duplicates(subset=['id'])
    df = df[df['id'] > 0]

    df['id'] = df['id'].astype('int64')
    df['views'] = df['views'].astype('int64')
    df['likes'] = df['likes'].astype('int64')

    # 重新分配顺序 ID (1,2,3...)
    df = df.reset_index(drop=True)
    df['id'] = range(1, len(df) + 1)
    df['id'] = df['id'].astype('int64')

    logging.info(f"多源抓取完成: {len(df)} 条不重复真实视频 (原始 {len(all_videos)} 条)")
    return df


def supplement_videos(existing_df: pd.DataFrame, target_total: int = 10000) -> pd.DataFrame:
    """基于真实数据分布补充模拟视频，达到 target_total"""
    existing_count = len(existing_df)
    need = target_total - existing_count
    if need <= 0:
        logging.info(f"已有 {existing_count} 条真实视频，无需补充")
        return existing_df

    logging.info(f"补充生成 {need} 条模拟视频 (真实 {existing_count} → 目标 {target_total})")

    rng = np.random.default_rng(42)
    tag_counts = existing_df['tag'].value_counts(normalize=True)
    tags = tag_counts.index.tolist()
    tag_probs = tag_counts.values

    real_views = existing_df['views'].astype(float)
    real_views_pos = real_views[real_views > 1000]
    if len(real_views_pos) > 30:
        log_views = np.log(real_views_pos)
        mu_views, sigma_views = log_views.mean(), log_views.std()
    else:
        mu_views, sigma_views = 10.0, 1.8

    sim_tags = rng.choice(tags, size=need, p=tag_probs)
    sim_views = np.exp(rng.normal(mu_views, sigma_views, need)).astype('int64')
    like_ratios = rng.beta(1.5, 30, need)
    sim_likes = (sim_views * like_ratios).astype('int64')

    next_id = existing_df['id'].max() + 1
    sim_df = pd.DataFrame({
        'id': range(next_id, next_id + need),
        'tag': sim_tags,
        'views': sim_views,
        'likes': sim_likes,
        'viewed_by': '[]',
        'liked_by': '[]'
    })

    result = pd.concat([existing_df, sim_df], ignore_index=True)
    result['id'] = range(1, len(result) + 1)
    result['id'] = result['id'].astype('int64')
    result['views'] = result['views'].astype('int64')
    result['likes'] = result['likes'].astype('int64')

    logging.info(f"补充完成: 真实 {existing_count} + 模拟 {need} = {len(result)} 条")
    return result


def crawl_and_save_video_data() -> None:
    try:
        videos_df = fetch_bilibili_videos()
        if videos_df.empty:
            logging.error("未能抓取到任何视频数据")
            return
        if not validate_video_data(videos_df):
            raise ValueError("数据验证失败")
        os.makedirs('data', exist_ok=True)
        videos_df.to_csv('data/bilibili_videos.csv', index=False, mode='w')
        logging.info(f"保存 {len(videos_df)} 条视频")
    except Exception as e:
        logging.error(f"失败: {e}")
        raise


if __name__ == '__main__':
    crawl_and_save_video_data()
