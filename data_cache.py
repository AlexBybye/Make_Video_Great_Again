# data_cache.py — 全局缓存（SQLite 优先，CSV 兜底）
import os
import logging
import database


class DataCache:
    _videos_df = None
    _operations_df = None
    _users_df = None
    _user_ids = None
    _use_db = True

    @classmethod
    def _init_db(cls):
        try:
            database.init_db()
            database.import_csv_if_empty()
            if database.table_count('videos') > 0:
                cls._use_db = True
                return True
        except Exception as e:
            logging.warning(f"数据库不可用，回退到 CSV: {e}")
        cls._use_db = False
        return False

    @classmethod
    def load_videos(cls):
        if cls._videos_df is None:
            if cls._use_db and database.table_count('videos') > 0:
                cls._videos_df = database.load_videos()
                logging.info("视频数据已从 SQLite 加载到缓存")
            else:
                import pandas as pd
                cls._videos_df = pd.read_csv('data/videos.csv')
                logging.info("视频数据已从 CSV 加载到缓存")
        return cls._videos_df

    @classmethod
    def load_operations(cls):
        if cls._operations_df is None:
            if cls._use_db and database.table_count('operations') > 0:
                cls._operations_df = database.load_operations()
                cls._user_ids = set(cls._operations_df['user_id'].astype(str))
                logging.info("操作数据已从 SQLite 加载到缓存")
            else:
                import pandas as pd
                cls._operations_df = pd.read_csv('data/operations.csv')
                cls._user_ids = set(cls._operations_df['user_id'].astype(str))
                logging.info("操作数据已从 CSV 加载到缓存")
        return cls._operations_df

    @classmethod
    def load_users(cls):
        if cls._users_df is None:
            if cls._use_db and database.table_count('users') > 0:
                cls._users_df = database.load_users()
                logging.info("用户数据已从 SQLite 加载到缓存")
            else:
                import pandas as pd
                cls._users_df = pd.read_csv('data/users.csv')
                logging.info("用户数据已从 CSV 加载到缓存")
        return cls._users_df

    @classmethod
    def preload_all(cls):
        if not cls._use_db:
            database.init_db()
            # 尝试从 CSV 导入到 DB
            csv_path = os.path.join('data', 'videos.csv')
            if os.path.exists(csv_path):
                try:
                    database.import_csv_if_empty()
                    cls._use_db = True
                except Exception as e:
                    logging.warning(f"CSV 导入 DB 失败: {e}")
                    cls._use_db = False
        cls.load_videos()
        cls.load_operations()
        cls.load_users()
        logging.info("所有数据预加载完成")

    @classmethod
    def clear_cache(cls):
        cls._videos_df = None
        cls._operations_df = None
        cls._users_df = None
        cls._user_ids = None
        cls._use_db = True
        cls._init_db()
        logging.info("缓存已清除并重新连接数据库")

    @classmethod
    def get_user_ids(cls):
        if cls._user_ids is None:
            cls.load_operations()
        return cls._user_ids

    @classmethod
    def check_data_files(cls):
        # 先检查数据库
        if cls._use_db and database.table_count('videos') > 0:
            return True
        # 再检查 CSV
        required = ['videos.csv', 'operations.csv', 'users.csv']
        for f in required:
            fp = os.path.join('data', f)
            if not os.path.exists(fp):
                return False
            try:
                import pandas as pd
                pd.read_csv(fp)
            except:
                return False
        return True
