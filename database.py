# database.py - SQLite 数据持久化层
import sqlite3
import pandas as pd
import os
import logging

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'app.db')

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """创建数据库表（如果不存在）"""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY,
            tag TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            viewed_by TEXT DEFAULT '[]',
            liked_by TEXT DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            age INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            liked INTEGER DEFAULT 0,
            day INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ops_user ON operations(user_id);
        CREATE INDEX IF NOT EXISTS idx_ops_video ON operations(video_id);

        CREATE TABLE IF NOT EXISTS users_clustered (
            id INTEGER PRIMARY KEY,
            age INTEGER,
            cluster INTEGER
        );
        CREATE TABLE IF NOT EXISTS videos_clustered (
            id INTEGER PRIMARY KEY,
            tag TEXT,
            views INTEGER,
            likes INTEGER,
            cluster INTEGER
        );
    """)
    conn.commit()
    conn.close()
    logging.info("数据库表初始化完成")


def table_exists(table_name):
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    exists = cur.fetchone()[0] > 0
    conn.close()
    return exists


def table_count(table_name):
    conn = get_conn()
    try:
        cur = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cur.fetchone()[0]
    except:
        return 0
    finally:
        conn.close()


def import_csv_if_empty():
    """如果数据库为空，从 CSV 导入数据"""
    init_db()

    # 导入 videos
    if table_count('videos') == 0:
        csv_path = os.path.join(os.path.dirname(DB_PATH), 'videos.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            conn = get_conn()
            df.to_sql('videos', conn, if_exists='append', index=False)
            conn.close()
            logging.info(f"从 CSV 导入 videos: {len(df)} 条")
        else:
            logging.warning("videos.csv 不存在，跳过导入")

    # 导入 users
    if table_count('users') == 0:
        csv_path = os.path.join(os.path.dirname(DB_PATH), 'users.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            conn = get_conn()
            df.to_sql('users', conn, if_exists='append', index=False)
            conn.close()
            logging.info(f"从 CSV 导入 users: {len(df)} 条")

    # 导入 operations
    if table_count('operations') == 0:
        csv_path = os.path.join(os.path.dirname(DB_PATH), 'operations.csv')
        if os.path.exists(csv_path):
            # 大文件分块导入
            conn = get_conn()
            for chunk in pd.read_csv(csv_path, chunksize=50000):
                chunk.to_sql('operations', conn, if_exists='append', index=False)
            conn.close()
            logging.info(f"从 CSV 导入 operations 完成")


def load_videos():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM videos", conn)
    conn.close()
    return df


def load_users():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM users", conn)
    conn.close()
    return df


def load_operations():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM operations", conn)
    conn.close()
    return df


def save_videos(df):
    conn = get_conn()
    df.to_sql('videos', conn, if_exists='replace', index=False)
    conn.close()


def save_users(df):
    conn = get_conn()
    df.to_sql('users', conn, if_exists='replace', index=False)
    conn.close()


def save_operations(df):
    conn = get_conn()
    df.to_sql('operations', conn, if_exists='replace', index=False)
    conn.close()


def save_clustered_users(df):
    conn = get_conn()
    df.to_sql('users_clustered', conn, if_exists='replace', index=False)
    conn.close()


def save_clustered_videos(df):
    conn = get_conn()
    df.to_sql('videos_clustered', conn, if_exists='replace', index=False)
    conn.close()


def get_user_ids():
    conn = get_conn()
    cur = conn.execute("SELECT DISTINCT user_id FROM operations")
    ids = {str(row[0]) for row in cur.fetchall()}
    conn.close()
    return ids


def clear_db():
    conn = get_conn()
    conn.executescript("""
        DROP TABLE IF EXISTS videos;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS operations;
        DROP TABLE IF EXISTS users_clustered;
        DROP TABLE IF EXISTS videos_clustered;
    """)
    conn.commit()
    conn.close()
    init_db()
