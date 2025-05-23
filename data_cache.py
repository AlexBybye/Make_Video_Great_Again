# data_cache.py —— 全局缓存与哈希索引

import pandas as pd
import logging
import os

class DataCache:
    """数据缓存管理类"""
    _instance = None
    
    # 类级别的缓存
    _videos_df = None
    _operations_df = None
    _users_df = None
    _user_ids = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load_videos(cls):
        """加载视频数据到缓存"""
        if cls._videos_df is None:
            try:
                cls._videos_df = pd.read_csv('data/videos.csv')
                logging.info("视频数据已加载到缓存")
            except Exception as e:
                logging.error(f"加载视频数据失败: {str(e)}")
                raise
        return cls._videos_df
    
    @classmethod
    def load_operations(cls):
        """加载操作数据到缓存"""
        if cls._operations_df is None:
            try:
                cls._operations_df = pd.read_csv('data/operations.csv')
                cls._user_ids = set(cls._operations_df['user_id'].astype(str))
                logging.info("操作数据已加载到缓存")
            except Exception as e:
                logging.error(f"加载操作数据失败: {str(e)}")
                raise
        return cls._operations_df
    
    @classmethod
    def load_users(cls):
        """加载用户数据到缓存"""
        if cls._users_df is None:
            try:
                cls._users_df = pd.read_csv('data/users.csv')
                logging.info("用户数据已加载到缓存")
            except Exception as e:
                logging.error(f"加载用户数据失败: {str(e)}")
                raise
        return cls._users_df
    
    @classmethod
    def preload_all(cls):
        """预加载所有数据"""
        try:
            cls.load_videos()
            cls.load_operations()
            cls.load_users()
            logging.info("所有数据预加载完成")
        except Exception as e:
            logging.error(f"数据预加载失败: {str(e)}")
            raise
    
    @classmethod
    def clear_cache(cls):
        """清除所有缓存"""
        cls._videos_df = None
        cls._operations_df = None
        cls._users_df = None
        cls._user_ids = None
        logging.info("缓存已清除")
    
    @classmethod
    def get_user_ids(cls):
        """获取用户ID集合"""
        if cls._user_ids is None:
            cls.load_operations()
        return cls._user_ids
    
    @classmethod
    def check_data_files(cls):
        """检查数据文件是否存在且有效"""
        required_files = ['videos.csv', 'operations.csv', 'users.csv']
        for file in required_files:
            file_path = os.path.join('data', file)
            if not os.path.exists(file_path):
                return False
            try:
                pd.read_csv(file_path)
            except Exception as e:
                logging.warning(f"文件 {file} 无效: {str(e)}")
                return False
        return True
