import sys
import os
import logging
from PyQt6.QtWidgets import QApplication

# 假设这两个模块包含爬取逻辑
# 请确保它们在同一目录下或PYTHONPATH中
# ⚠️ 如果您的爬虫文件命名不同，请修改这里
import capture_videos  # 假设包含 crawl_and_save_video_data()
import capture_users_operation  # 假设包含 crawl_and_save_bilibili_data()

from data_manager import DataManager
from ui import LoadingSplash, MainWindow

# 配置日志（可选，但推荐）
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def check_and_crawl_data():
    """
    检查数据文件是否存在，如果不存在则调用爬虫进行爬取。
    """
    DATA_DIR = 'data'
    BILIBILI_VIDEOS_FILE = os.path.join(DATA_DIR, 'bilibili_videos.csv')
    BILIBILI_OPERATIONS_FILE = os.path.join(DATA_DIR, 'bilibili_user_operation.csv')

    # 确保 data 目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs("results", exist_ok=True)  # 保持原 main.py 的逻辑

    # 1. 检查并爬取视频数据 (bilibili_videos.csv)
    if not os.path.exists(BILIBILI_VIDEOS_FILE):
        print(f"--- [数据检测] 缺失文件：{BILIBILI_VIDEOS_FILE} 不存在，开始爬取... ---")
        try:
            # 调用 capture_videos.py 中的主函数
            capture_videos.crawl_and_save_video_data()
            print(f"--- [数据检测] 视频数据爬取完成 ---")
        except Exception as e:
            print(f"--- [错误] 视频数据爬取失败: {e} ---")
            logging.error(f"视频数据爬取失败: {e}")
    else:
        print(f"--- [数据检测] 文件存在：{BILIBILI_VIDEOS_FILE}。跳过爬取。 ---")

    # 2. 检查并爬取用户操作数据 (bilibili_user_operation.csv)
    if not os.path.exists(BILIBILI_OPERATIONS_FILE):
        print(f"--- [数据检测] 缺失文件：{BILIBILI_OPERATIONS_FILE} 不存在，开始爬取... ---")
        try:
            # 调用 capture_users_operation.py 中的主函数
            capture_users_operation.crawl_and_save_bilibili_data()
            print(f"--- [数据检测] 操作数据爬取完成 ---")
        except Exception as e:
            print(f"--- [错误] 操作数据爬取失败: {e} ---")
            logging.error(f"操作数据爬取失败: {e}")
    else:
        print(f"--- [数据检测] 文件存在：{BILIBILI_OPERATIONS_FILE}。跳过爬取。 ---")


# ==============================================================================
# 应用程序启动入口
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 初始化闪屏 (用于显示加载过程)
    splash = LoadingSplash()
    splash.show()
    # 强制刷新界面，显示闪屏
    QApplication.processEvents()

    # --- 💥 在加载 UI/数据之前，执行数据检测和爬取逻辑 💥 ---
    # 这确保了在 DataManager 尝试加载文件之前，文件是存在的
    check_and_crawl_data()

    # 初始化数据管理器（此时数据文件已确保存在或已尝试爬取）
    DataManager()

    # 爬取/数据加载完毕，关闭闪屏
    splash.close()

    # 显示主界面
    window = MainWindow()
    window.show()

    sys.exit(app.exec())