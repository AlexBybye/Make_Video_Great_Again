from arima import ARIMA  # 确保正确导入 ARIMA 类

class VideoHeatPredictor:
    def __init__(self, videos):
        self.videos = videos

    def predict_heat(self, video_id, future_days=5):
        video = next(video for video in self.videos if video.video_id == video_id)

        # 获取历史热度数据（点赞 + 评论 + 分享）
        heat_trend = [
            likes + comments + shares
            for likes, comments, shares in zip(video.like_trend, video.comment_trend, video.share_trend)
        ]

        # 数据长度校验
        min_required_length = 2  # 至少需要 2 个数据点
        if len(heat_trend) < min_required_length:
            return f"至少需要 {min_required_length} 天数据，当前仅有 {len(heat_trend)} 天数据"

        # 数据合理性校验
        if max(heat_trend) == 0:
            return "历史热度数据为零，无法预测"

        try:
            # 使用 ARIMA 模型（降低阶数）
            model = ARIMA(order=(1, 0, 0))  # 更简单的 AR(1) 模型
            model.fit(heat_trend)
            future_heat = model.forecast(steps=future_days)
            return future_heat
        except Exception as e:
            return f"预测失败: {str(e)}"