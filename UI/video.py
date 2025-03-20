class Video:
    def __init__(self, video_id, category):
        self.video_id = video_id
        self.category = category
        self.likes = 0
        self.comments = 0
        self.shares = 0
        self.like_trend = [0] * 5  # 初始化长度为 5 的数组，存储每天的行为数据
        self.comment_trend = [0] * 5
        self.share_trend = [0] * 5

    def like(self, date):
        self.likes += 1
        self.like_trend[date] += 1

    def comment(self, date):
        self.comments += 1
        self.comment_trend[date] += 1

    def share(self, date):
        self.shares += 1
        self.share_trend[date] += 1

    def get_stats(self):
        return {
            "video_id": self.video_id,
            "category": self.category,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "like_trend": self.like_trend,
            "comment_trend": self.comment_trend,
            "share_trend": self.share_trend
        }