import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import IncrementalPCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

class VideoCluster:
    def __init__(self, users, videos, user_video_matrix):
        self.users = users
        self.videos = videos
        self.user_video_matrix = user_video_matrix  # 使用传入的交互矩阵

    def cluster_videos(self, n_clusters=3):
        """对视频进行聚类"""
        video_user_matrix = self.user_video_matrix.T  # 转置为用户-视频交互矩阵

        # 标准化数据
        scaler = StandardScaler(with_mean=False)
        video_user_matrix_scaled = scaler.fit_transform(video_user_matrix)

        # 使用增量 PCA 降维
        pca = IncrementalPCA(n_components=2, batch_size=1000)
        video_user_matrix_reduced = pca.fit_transform(video_user_matrix_scaled.toarray())

        # 使用 MiniBatchKMeans 聚类
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=1000)
        video_labels = kmeans.fit_predict(video_user_matrix_reduced)

        return video_labels, video_user_matrix_reduced

    def plot_video_clusters(self, video_labels, video_user_matrix_reduced):
        """绘制视频聚类结果的散点图"""
        plt.figure(figsize=(8, 6))
        plt.scatter(video_user_matrix_reduced[:, 0], video_user_matrix_reduced[:, 1], c=video_labels, cmap='viridis', marker='o', s=50)
        plt.title("Video Clustering Results")
        plt.xlabel("PCA Component 1")
        plt.ylabel("PCA Component 2")
        plt.colorbar(label="Cluster Label")
        plt.grid(True)
        plt.show()


class UserCluster:
    def __init__(self, users, videos, user_video_matrix):
        self.users = users
        self.videos = videos
        self.user_video_matrix = user_video_matrix  # 直接使用传入的交互矩阵

    def cluster_users(self, n_clusters=3):
        """对用户进行聚类"""
        # 标准化数据
        scaler = StandardScaler(with_mean=False)
        user_video_matrix_scaled = scaler.fit_transform(self.user_video_matrix)

        # 使用增量 PCA 降维
        pca = IncrementalPCA(n_components=2, batch_size=1000)
        user_video_matrix_reduced = pca.fit_transform(user_video_matrix_scaled.toarray())

        # 使用 MiniBatchKMeans 聚类
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=1000)
        user_labels = kmeans.fit_predict(user_video_matrix_reduced)

        return user_labels, user_video_matrix_reduced

    def plot_user_clusters(self, user_labels, user_video_matrix_reduced):
        """绘制用户聚类结果的散点图"""
        plt.figure(figsize=(8, 6))
        plt.scatter(user_video_matrix_reduced[:, 0], user_video_matrix_reduced[:, 1], c=user_labels, cmap='viridis', marker='o', s=50)
        plt.title("User Clustering Results")
        plt.xlabel("PCA Component 1")
        plt.ylabel("PCA Component 2")
        plt.colorbar(label="Cluster Label")
        plt.grid(True)
        plt.show()