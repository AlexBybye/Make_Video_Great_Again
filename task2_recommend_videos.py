# -*- coding: utf-8 -*-
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

def recommend_videos(target_user_id):
    #"""任务2：推荐相关视频"""
    # 加载数据
    videos_df = pd.read_csv('videos.csv')
    operations_df = pd.read_csv('operations.csv')

    # 获取用户已观看的视频
    user_viewed_videos = operations_df[operations_df['user_id'] == target_user_id]['video_id'].unique()

    # 构建用户-标签矩阵（复用任务1的代码逻辑）
    operations_with_tag = operations_df.merge(
        videos_df[['id', 'tag']], 
        left_on='video_id', 
        right_on='id', 
        how='left'
    )
    user_tag_scores = operations_with_tag.groupby(['user_id', 'tag']).apply(
        lambda x: len(x) + x['liked'].sum()
    ).reset_index(name='score')
    user_tag_matrix = user_tag_scores.pivot(
        index='user_id', 
        columns='tag', 
        values='score'
    ).fillna(0)

    # 计算余弦相似度获取相似用户（前50个）
    user_vector = user_tag_matrix.loc[[target_user_id]].values
    similarities = cosine_similarity(user_vector, user_tag_matrix.values)
    similarities_series = pd.Series(similarities[0], index=user_tag_matrix.index)
    similar_users = similarities_series.sort_values(ascending=False).iloc[1:51].index.tolist()

    # 筛选候选视频
    similar_users_ops = operations_df[operations_df['user_id'].isin(similar_users)]
    candidate_videos = similar_users_ops[~similar_users_ops['video_id'].isin(user_viewed_videos)]['video_id']

    # 统计视频热度和标签匹配度
    video_heat = candidate_videos.value_counts().reset_index(name='count')
    recommend_df = pd.merge(video_heat, videos_df[['id', 'tag']], left_on='video_id', right_on='id', how='left')
    recommend_df['tag_score'] = recommend_df['tag'].map(
        lambda t: user_tag_matrix.loc[target_user_id, t] if t in user_tag_matrix.columns else 0
    )
    recommend_df['combined_score'] = recommend_df['count'] * recommend_df['tag_score']

    # 返回结果（格式：字典列表）
    top_recommendations = recommend_df.sort_values('combined_score', ascending=False).head(10)
    result = [
        {u"Video_ID": row['video_id'], u"label": row['tag'], u"Overall_rating": round(row['combined_score'], 2)}
        for _, row in top_recommendations.iterrows()
    ]
    return result