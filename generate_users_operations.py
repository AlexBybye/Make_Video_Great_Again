# -*- coding: utf-8 -*-
import pandas as pd
import random
import numpy as np
from generate_videos import generate_videos

def generate_day_weights(force=False):
    # ���������Ȩ�أ�ÿ��Ȩ�ز�����0.1�Ҳ�����0.4
    weights = np.random.uniform(0.1, 0.4, 7)
    weights /= weights.sum()  # ��һ��ȷ���ܺ�Ϊ1
    return weights

def generate_days(num_ops,force=False):
    # ����������ɵ�Ȩ�ط�������
    weights = generate_day_weights()
    
    # ����Ȩ��������������
    days = np.random.choice(np.arange(1, 8), num_ops, p=weights)
    
    # ��ʱ��˳������
    days = np.sort(days)
    
    return days.tolist()

def generate_users_operations(force=False):
    # ���ò���
    num_users = 10_000
    num_videos = 100_000
    min_ops, max_ops = 100, 200
    
    # ��ʼ���û����䣬������̬�ֲ�������ʵ�����
    ages = np.random.normal(loc=35, scale=10, size=num_users)  # ��ֵ35����׼��10
    ages = np.clip(ages, 18, 60).astype(int)  # �������䷶Χ��18-60��
    
    users = pd.DataFrame({
        'id': range(1, num_users + 1),
        'age': ages
    })
    
    # ��ʼ����Ƶͳ����Ϣ����NumPy���٣�
    views = np.zeros(num_videos, dtype=int)
    likes = np.zeros(num_videos, dtype=int)
    
    # ��ȡ��Ƶ����
    videos = pd.read_csv('data/videos.csv')  # 原路径为'videos.csv'
    viewed_by = videos['viewed_by'].apply(eval).tolist()  # ���ַ���ת��Ϊ�б�
    liked_by = videos['liked_by'].apply(eval).tolist()  # ���ַ���ת��Ϊ�б�
    
    # ���ɲ�����¼
    operations = []
    for user_id in users['id']:
        num_ops = random.randint(min_ops, max_ops)
        days = generate_days(num_ops)
        
        for day in days:
            video_id = random.randint(1, num_videos)
            video_idx = video_id - 1
            
            # ��������͵���
            views[video_idx] += 1
            if random.random() < 0.3:  # 30%���ʵ���
                likes[video_idx] += 1
                liked = 1
                # ��¼�����û�������
                liked_by[video_idx].append((user_id, day))
            else:
                liked = 0
            
            # ��¼����������day�ֶΣ�
            operations.append({
                'user_id': user_id,
                'video_id': video_id,
                'liked': liked,
                'day': day
            })
            
            # ��¼�ۿ��û�������
            viewed_by[video_idx].append((user_id, day))
    
    # �����û���Ϣ
    users.to_csv('data/users.csv', index=False, mode='w')
    
    # ���������¼
    pd.DataFrame(operations).to_csv('data/operations.csv', index=False, mode='w')
    
    # ������Ƶͳ����Ϣ������
    videos['views'] = views
    videos['likes'] = likes
    videos['viewed_by'] = viewed_by
    videos['liked_by'] = liked_by
    videos.to_csv('data/videos.csv', index=False, mode='w')
