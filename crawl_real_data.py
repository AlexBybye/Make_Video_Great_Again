# crawl_real_data.py
# 统一爬取 B站真实数据并存入系统所需的文件格式
import os
import logging
import threading
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局进度状态（线程安全）
_progress_lock = threading.Lock()
crawl_progress = {
    "running": False,
    "phase": "idle",
    "phase_text": "",
    "percent": 0,
    "detail": "",
    "videos_count": 0,
    "users_count": 0,
    "operations_count": 0,
    "error": None
}


def _update_progress(**kwargs):
    with _progress_lock:
        crawl_progress.update(kwargs)


def crawl_and_save_all():
    """完整流程：抓取B站视频 → 生成用户+操作 → 保存为系统格式"""
    import capture_videos
    import capture_users_operation

    _update_progress(running=True, phase="init", phase_text="初始化", percent=5, detail="准备开始抓取...",
                     videos_count=0, users_count=0, operations_count=0, error=None)

    os.makedirs('data', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    # ===== 步骤1：抓取B站视频（带分类标签）=====
    logging.info("========== 步骤1：抓取B站视频数据 ==========")
    _update_progress(phase="fetch_videos", phase_text="抓取B站视频数据", percent=10, detail="正在连接B站API...")
    try:
        bilibili_videos = capture_videos.fetch_bilibili_videos(
            progress_callback=lambda pct, detail, vcount: _update_progress(
                phase="fetch_videos", phase_text="抓取B站视频数据",
                percent=10 + int(pct * 0.45), detail=detail,
                videos_count=vcount
            )
        )
        if bilibili_videos.empty:
            _update_progress(running=False, error="未抓取到视频数据，请检查网络连接")
            return {"success": False, "error": "未抓取到视频数据，请检查网络连接"}

        videos_df = bilibili_videos[['id', 'tag', 'views', 'likes', 'viewed_by', 'liked_by']]
        _update_progress(videos_count=len(videos_df), percent=30,
                        detail=f"B站抓取完成 {len(videos_df)} 条，补充生成模拟视频...")
        logging.info(f"B站视频数据: {len(videos_df)} 条")

        # 补充生成模拟视频到10万条
        _update_progress(phase="supplement", phase_text="补充生成视频到10万", percent=35)
        videos_df = capture_videos.supplement_videos(videos_df, target_total=100000)
        videos_df.to_csv('data/videos.csv', index=False)
        _update_progress(videos_count=len(videos_df), percent=55,
                        detail=f"视频总数: {len(videos_df)} (真实+模拟)")
        logging.info(f"视频数据已保存: data/videos.csv ({len(videos_df)} 条)")
    except Exception as e:
        logging.error(f"视频抓取失败: {e}")
        _update_progress(running=False, error=str(e))
        return {"success": False, "error": f"视频抓取失败: {str(e)}"}

    # ===== 步骤2：基于真实视频生成用户和操作数据 =====
    logging.info("========== 步骤2：生成用户和操作数据 ==========")
    _update_progress(phase="gen_users", phase_text="生成用户和操作数据", percent=58, detail="正在模拟生成用户...")
    try:
        video_ids = videos_df['id'].tolist()

        _update_progress(percent=60, detail="生成10000个模拟用户...")
        users_df, operations_df = capture_users_operation.generate_users_and_operations(
            pd.DataFrame({'video_id': video_ids})
        )

        if users_df.empty or operations_df.empty:
            _update_progress(running=False, error="生成用户/操作数据为空")
            return {"success": False, "error": "生成用户/操作数据为空"}

        _update_progress(percent=75, users_count=len(users_df), operations_count=len(operations_df),
                        detail=f"已生成 {len(users_df)} 用户, {len(operations_df)} 条操作")

        if not capture_users_operation.validate_user_data(users_df):
            _update_progress(running=False, error="用户数据验证失败")
            return {"success": False, "error": "用户数据验证失败"}
        if not capture_users_operation.validate_operations_data(operations_df):
            _update_progress(running=False, error="操作数据验证失败")
            return {"success": False, "error": "操作数据验证失败"}

        users_df.to_csv('data/users.csv', index=False)
        operations_df.to_csv('data/operations.csv', index=False)
        logging.info(f"用户数据已保存: data/users.csv ({len(users_df)} 条)")
        logging.info(f"操作数据已保存: data/operations.csv ({len(operations_df)} 条)")
    except Exception as e:
        logging.error(f"用户/操作数据生成失败: {e}")
        _update_progress(running=False, error=str(e))
        return {"success": False, "error": f"用户/操作数据生成失败: {str(e)}"}

    # ===== 步骤3：同步到 SQLite 数据库 =====
    _update_progress(phase="save_db", phase_text="同步数据库", percent=85, detail="保存到SQLite...")
    try:
        import database
        database.save_videos(videos_df)
        database.save_users(users_df)
        database.save_operations(operations_df)
        logging.info("数据已同步到 SQLite 数据库")
    except Exception as e:
        logging.warning(f"数据库同步警告: {e}")

    # ===== 步骤4：清除缓存，重新加载 =====
    _update_progress(phase="refresh_cache", phase_text="刷新缓存", percent=92, detail="预加载数据缓存...")
    try:
        from data_cache import DataCache
        DataCache.clear_cache()
        DataCache.preload_all()
        logging.info("数据缓存已刷新")
    except Exception as e:
        logging.warning(f"缓存刷新警告: {e}")

    _update_progress(phase="done", phase_text="完成", percent=100, detail="数据抓取完成!", running=False)

    return {
        "success": True,
        "videos_count": len(videos_df),
        "users_count": len(users_df),
        "operations_count": len(operations_df)
    }


if __name__ == '__main__':
    result = crawl_and_save_all()
    if result["success"]:
        print(f"\n完成！视频:{result['videos_count']} 用户:{result['users_count']} 操作:{result['operations_count']}")
    else:
        print(f"\n失败: {result['error']}")
