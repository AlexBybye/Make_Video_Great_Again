#import os
import os
import sys

import pandas as pd
from PyQt6.QtWidgets import QMessageBox
import generate_videos
import generate_users_operations

class DataManager:
    """ 数据管理单例类（每次运行强制重新生成数据） """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init_data()
        return cls._instance

    def _init_data(self):
        """ 初始化数据（强制重新生成） """
        try:
            # 创建数据目录
            os.makedirs("data", exist_ok=True)
            os.makedirs("results", exist_ok=True)

            # 强制重新生成数据
            self._generate_initial_data()  # 移除原有的条件判断

            # 加载新生成的数据
            self.operations_df = pd.read_csv("data/operations.csv")
            self.user_ids = set(self.operations_df['user_id'].astype(str))

        except Exception as e:
            QMessageBox.critical(None, "数据错误", f"数据生成失败: {str(e)}")
            sys.exit(1)

    def _generate_initial_data(self):
        """ 生成初始数据（强制覆盖旧文件） """
        # 生成视频数据（示例实现）
        generate_videos.generate_videos(force=True)
        # 生成用户操作数据（示例实现）
        generate_users_operations.generate_users_operations(force=True)