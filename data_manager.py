import os
import sys
import time
import pandas as pd
from PyQt6.QtWidgets import QMessageBox
import generate_videos
import generate_users_operations
import logging
from data_cache import DataCache

# 配置日志
logging.basicConfig(
    filename='data_manager.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DataManager:
    """ 数据管理单例类（使用缓存机制） """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init_data()
        return cls._instance

    def _init_data(self):
        """ 初始化数据（使用缓存机制） """
        t1 = time.time()
        try:
            # 创建数据目录
            os.makedirs("data", exist_ok=True)
            os.makedirs("results", exist_ok=True)

            # 检查数据文件是否存在且有效
            if not DataCache.check_data_files():
                logging.info("数据文件不存在或无效，开始生成新数据")
                self._generate_initial_data()
            else:
                logging.info("使用现有数据文件")

            # 预加载数据到缓存
            DataCache.preload_all()

        except Exception as e:
            error_msg = f"数据初始化失败: {str(e)}"
            logging.error(error_msg)
            QMessageBox.critical(None, "数据错误", error_msg)
            sys.exit(1)

        t2 = time.time()
        print(f"初始化数据耗时: {t2 - t1:.4f} 秒")

    def _generate_initial_data(self):
        """ 生成初始数据（仅在必要时） """

        try:
            t1 = time.time()
            logging.info("开始生成视频数据")
            generate_videos.generate_videos(force=True)
            
            logging.info("开始生成用户操作数据")
            generate_users_operations.generate_users_operations(force=True)
            
            logging.info("数据生成完成")
            t2 = time.time()
            print(f"生成数据耗时: {t2 - t1:.4f} 秒")
        except Exception as e:
            logging.error(f"数据生成失败: {str(e)}")
            raise



    @property
    def videos_df(self):
        """ 获取视频数据（从缓存） """
        return DataCache.load_videos()

    @property
    def operations_df(self):
        """ 获取操作数据（从缓存） """
        return DataCache.load_operations()

    @property
    def users_df(self):
        """ 获取用户数据（从缓存） """
        return DataCache.load_users()

    @property
    def user_ids(self):
        """ 获取用户ID集合（从缓存） """
        return DataCache.get_user_ids()

    def clear_cache(self):
        """ 清除缓存数据 """
        DataCache.clear_cache()
        logging.info("缓存已清除")