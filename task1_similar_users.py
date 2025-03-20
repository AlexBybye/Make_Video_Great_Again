# -*- coding: utf-8 -*-
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def find_similar_users(target_user_id):
    #"""任务1：查找相似用户群体"""
    # 加载数据
    videos_df = pd.read_csv('data/videos.csv')
    operations_df = pd.read_csv('data/operations.csv')

    # 合并操作记录与视频标签
    operations_with_tag = operations_df.merge(
        videos_df[['id', 'tag']], 
        left_on='video_id', 
        right_on='id', 
        how='left'
    )

    # 构建用户-标签矩阵
    user_tag_scores = operations_with_tag.groupby(['user_id', 'tag']).apply(
        lambda x: len(x) + x['liked'].sum()
    ).reset_index(name='score')
    user_tag_matrix = user_tag_scores.pivot(
        index='user_id', 
        columns='tag', 
        values='score'
    ).fillna(0)

    # 计算余弦相似度
    user_vector = user_tag_matrix.loc[[target_user_id]].values
    similarities = cosine_similarity(user_vector, user_tag_matrix.values)
    similarities_series = pd.Series(similarities[0], index=user_tag_matrix.index)

    # 取前5个相似用户（排除自己）
    top_similar_users = similarities_series.sort_values(ascending=False).iloc[1:6]

    # 返回结果（格式：字典列表）
    result = [
        {u"user_ID": user_id, u"similarity": round(similarity, 4)}
        for user_id, similarity in top_similar_users.items()
    ]
    return result