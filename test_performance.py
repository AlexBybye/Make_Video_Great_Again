import time
import logging
from task1_similar_users import find_similar_users
from task2_recommend_videos import recommend_videos

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_tasks(user_id):
    """测试任务1和任务2的执行时间"""
    
    # 测试任务1
    start_time = time.time()
    try:
        similar_users = find_similar_users(user_id)
        task1_time = time.time() - start_time
        print(f"\n任务1执行时间: {task1_time:.2f} 秒")
        print("相似用户结果:", similar_users)
    except Exception as e:
        print(f"任务1执行失败: {str(e)}")
        return

    # 测试任务2
    start_time = time.time()
    try:
        recommendations = recommend_videos(user_id)
        task2_time = time.time() - start_time
        print(f"\n任务2执行时间: {task2_time:.2f} 秒")
        print("推荐视频结果:", recommendations)
    except Exception as e:
        print(f"任务2执行失败: {str(e)}")
        return

    # 显示总时间
    total_time = task1_time + task2_time
    print(f"\n总执行时间: {total_time:.2f} 秒")

if __name__ == "__main__":
    # 测试用户ID
    test_user_id = 1
    print(f"\n开始测试用户 {test_user_id} 的推荐...\n")
    test_tasks(test_user_id) 