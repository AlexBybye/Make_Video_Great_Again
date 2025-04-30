# -*- coding: utf-8 -*-
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

def recommend_videos(target_user_id):
    #"""����2���Ƽ������Ƶ"""
    # ��������
    videos_df = pd.read_csv('data/videos.csv')  # 原路径为'videos.csv'
    operations_df = pd.read_csv('data/operations.csv')  # 原路径为'operations.csv'

    # ��ȡ�û��ѹۿ�����Ƶ
    user_viewed_videos = operations_df[operations_df['user_id'] == target_user_id]['video_id'].unique()

    # �����û�-��ǩ���󣨸�������1�Ĵ����߼���
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

    # �����������ƶȻ�ȡ�����û���ǰ50����
    user_vector = user_tag_matrix.loc[[target_user_id]].values
    similarities = cosine_similarity(user_vector, user_tag_matrix.values)
    similarities_series = pd.Series(similarities[0], index=user_tag_matrix.index)
    similar_users = similarities_series.sort_values(ascending=False).iloc[1:51].index.tolist()

    # ɸѡ��ѡ��Ƶ
    similar_users_ops = operations_df[operations_df['user_id'].isin(similar_users)]
    candidate_videos = similar_users_ops[~similar_users_ops['video_id'].isin(user_viewed_videos)]['video_id']

    # ͳ����Ƶ�ȶȺͱ�ǩƥ���
    video_heat = candidate_videos.value_counts().reset_index(name='count')
    recommend_df = pd.merge(video_heat, videos_df[['id', 'tag']], left_on='video_id', right_on='id', how='left')
    recommend_df['tag_score'] = recommend_df['tag'].map(
        lambda t: user_tag_matrix.loc[target_user_id, t] if t in user_tag_matrix.columns else 0
    )
    recommend_df['combined_score'] = recommend_df['count'] * recommend_df['tag_score']

    # ���ؽ������ʽ���ֵ��б�
    top_recommendations = recommend_df.sort_values('combined_score', ascending=False).head(10)
    result = [
        {u"Video_ID": row['video_id'], u"label": row['tag'], u"Overall_rating": round(row['combined_score'], 2)}
        for _, row in top_recommendations.iterrows()
    ]
    return result