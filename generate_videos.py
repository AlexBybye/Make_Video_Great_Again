# -*- coding: utf-8 -*-
import pandas as pd
import random

def generate_videos(force=False):
    tags = ['movie', 'music', 'game', 'life', 'tech', 'fashion', 'sports', 'food', 'education', 'travel']
    num_videos = 100_000
    
    # ������Ƶ�б�����ǩ��
    video_tags = [random.choice(tags) for _ in range(num_videos)]
    
    # ��ʼ��ÿ����Ƶ�Ĺۿ���¼�͵��޼�¼���û�ID�����ڣ�
    viewed_by = [[] for _ in range(num_videos)]
    liked_by = [[] for _ in range(num_videos)]
    
    # ���浽DataFrame
    df = pd.DataFrame({
        'id': range(1, num_videos + 1),
        'tag': video_tags,
        'views': 0,  # ��ʼֵ������ͨ��������¼����
        'likes': 0,
        'viewed_by': viewed_by,  # ��¼ÿ����Ƶ�����챻��Щ�û��ۿ�
        'liked_by': liked_by  # ��¼ÿ����Ƶ�����챻��Щ�û�����
    })
    df.to_csv('data/videos.csv', index=False,mode='w')

