# -*- coding: utf-8 -*-
# import generate_videos
# import generate_users_operations

# if __name__ == '__main__':
#     # 先生成视频基础信息
#     generate_videos.generate_videos()
    
#     # 再生成用户和操作记录（自动更新视频统计）
#     generate_users_operations.generate_users_operations()

# import generate_videos
# import generate_users_operations
# import task1_similar_users
# import task2_recommend_videos
# import argparse

# if __name__ == '__main__':
#     # 1. 生成基础数据
#     generate_videos.generate_videos()
#     generate_users_operations.generate_users_operations()

#     # 2. 解析命令行参数
#     parser = argparse.ArgumentParser(description='User_interest_analysis_and_recommendation')
#     parser.add_argument('--user_id', type=int, required=True, help='Target_User_ID')
#     args = parser.parse_args()

#     # 3. 执行任务1：查找相似用户
#     similar_users = task1_similar_users.find_similar_users(args.user_id)
#     print("\ntask1:Similar_user_groups")
#     print("user_ID | similarity")
#     for user in similar_users:
#         print(f"{user['user_ID']} | {user['similarity']:.4f}")

#     # 4. 执行任务2：推荐视频
#     recommendations = task2_recommend_videos.recommend_videos(args.user_id)
#     print("\ntask1:Featured_Video")
#     print("Video_ID | label | Overall_rating")
#     for video in recommendations:
#         print(f"{video['Video_ID']} | {video['label']} | {video['Overall_rating']:.2f}")

import generate_videos
import generate_users_operations
import task1_similar_users
import task2_recommend_videos
import pandas as pd

def main():
    # 1. 生成基础数据
    generate_videos.generate_videos()
    generate_users_operations.generate_users_operations()

    # 2. 加载用户列表用于验证
    operations_df = pd.read_csv('operations.csv')
    existing_user_ids = operations_df['user_id'].unique()
    while 1:
      choose_functions=input(u"\nPlease choose a function:").strip()
      if choose_functions =='1':
    # 3. 循环输入用户ID
        user_input = input(u"\nPlease enter the user ID (enter q to exit): ").strip()
        if user_input.lower() == 'q':
            break

        # 验证输入是否为整数
        try:
            user_id = int(user_input)
        except ValueError:
            print(u"Error: Enter a number or q to exit.")
            continue

        # 验证用户是否存在
        if user_id not in existing_user_ids:
            print(u"Error: User ID does not exist.")
            continue

        # 执行任务1
        similar_users = task1_similar_users.find_similar_users(user_id)
        print(u"\ntask1:Similar_user_groups")
        print(u"user_ID | similarity")
        for user in similar_users:
            print(u"{0} | {1:.4f}".format(user[u'user_ID'], user[u'similarity']))
        continue

      if choose_functions =='2':
      
        user_input = input(u"\nPlease enter the user ID (enter q to exit): ").strip()
        if user_input.lower() == 'q':
            break

        # 验证输入是否为整数
        try:
            user_id = int(user_input)
        except ValueError:
            print(u"Error: Enter a number or q to exit.")
            continue

        # 验证用户是否存在
        if user_id not in existing_user_ids:
            print(u"Error: User ID does not exist.")
            continue
        
        # 执行任务2
        recommendations = task2_recommend_videos.recommend_videos(user_id)
        print(u"\ntask2:Featured_Video")
        print(u"Video_ID | label | Overall_rating")
        for video in recommendations:
            print(u"{0} | {1} | {2:.2f}".format(video[u'Video_ID'], video[u'label'], video[u'Overall_rating']))
        continue
      if choose_functions =='q':
          break
      else:
          print(u"Error: choose a function or q to exit.")
          continue

if __name__ == '__main__':
    main()