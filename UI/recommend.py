from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class Recommender:
    def __init__(self, users, videos, user_video_matrix):
        self.users = users
        self.videos = videos
        self.user_video_matrix = user_video_matrix  # 直接使用传入的交互矩阵

        # 动态获取所有视频的分类标签，避免硬编码
        self.categories = list({video.category for video in self.videos})
        self.category_to_index = {category: idx for idx, category in enumerate(self.categories)}

        # 构建视频 ID 到列索引的映射
        self.video_id_to_col = {video.video_id: i for i, video in enumerate(self.videos)}

        # 构建用户-分类偏好向量
        self.user_category_vectors = self._build_category_vectors()

    def _build_category_vectors(self):
        """构建用户-分类偏好向量"""
        # 构建视频-分类矩阵（One-Hot 编码）
        video_category_matrix = np.zeros((len(self.videos), len(self.categories)))
        for i, video in enumerate(self.videos):
            category_idx = self.category_to_index[video.category]
            video_category_matrix[i, category_idx] = 1

        # 用户-分类偏好 = 用户-视频交互矩阵 × 视频-分类矩阵
        return self.user_video_matrix.dot(video_category_matrix)

    def find_similar_users(self, target_uid, top_n=5):
        """基于余弦相似度查找相似用户"""
        target_row = [user.uid for user in self.users].index(target_uid)
        target_vector = self.user_category_vectors[target_row].reshape(1, -1)
        similarities = cosine_similarity(target_vector, self.user_category_vectors)[0]

        # 排除自身并返回 Top-N
        sorted_indices = np.argsort(similarities)[::-1]
        similar_indices = [i for i in sorted_indices if i != target_row][:top_n]
        return [self.users[i].uid for i in similar_indices]

    def recommend_videos(self, target_uid, top_n=5):
        """基于分类偏好和视频热度推荐"""
        target_row = [user.uid for user in self.users].index(target_uid)
        favorite_category_idx = np.argmax(self.user_category_vectors[target_row])
        favorite_category = self.categories[favorite_category_idx]

        # 筛选未交互的视频并按热度排序
        candidate_videos = [
            video for video in self.videos
            if video.category == favorite_category
               and self.user_video_matrix[target_row, self.video_id_to_col[video.video_id]] == 0
        ]
        candidate_videos.sort(key=lambda x: x.likes + x.comments + x.shares, reverse=True)
        return [video.video_id for video in candidate_videos[:top_n]]