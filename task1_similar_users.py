# -*- coding: utf-8 -*-
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def find_similar_users(target_user_id):
    #"""����1�����������û�Ⱥ��"""
    # ��������
    videos_df = pd.read_csv('data/videos.csv')
    operations_df = pd.read_csv('data/operations.csv')

    # �ϲ�������¼����Ƶ��ǩ
    operations_with_tag = operations_df.merge(
        videos_df[['id', 'tag']], 
        left_on='video_id', 
        right_on='id', 
        how='left'
    )

    # �����û�-��ǩ����
    user_tag_scores = operations_with_tag.groupby(['user_id', 'tag']).apply(
        lambda x: len(x) + x['liked'].sum()
    ).reset_index(name='score')
    user_tag_matrix = user_tag_scores.pivot(
        index='user_id', 
        columns='tag', 
        values='score'
    ).fillna(0)

    # �����������ƶ�
    user_vector = user_tag_matrix.loc[[target_user_id]].values
    similarities = cosine_similarity(user_vector, user_tag_matrix.values)
    similarities_series = pd.Series(similarities[0], index=user_tag_matrix.index)

    # ȡǰ5�������û����ų��Լ���
    top_similar_users = similarities_series.sort_values(ascending=False).iloc[1:6]

    # ���ؽ������ʽ���ֵ��б�
    result = [
        {u"user_ID": user_id, u"similarity": round(similarity, 4)}
        for user_id, similarity in top_similar_users.items()
    ]
    return result