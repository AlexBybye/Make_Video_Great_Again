# task3_predict_heat.py
# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from PyQt6.QtGui import QPixmap

plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体或其他支持中文的字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def predict_video_heat(video_id):
    """ 使用ARIMA模型预测视频热度 """
    try:
        # 读取数据
        ops_df = pd.read_csv('data/operations.csv')
        videos_df = pd.read_csv('data/videos.csv')

        # 验证视频是否存在
        if video_id not in videos_df['id'].values:
            raise ValueError("视频ID不存在")

        # 获取历史数据（按天统计）
        video_ops = ops_df[ops_df['video_id'] == video_id]
        daily_views = video_ops.groupby('day').size().reindex(range(1, 8), fill_value=0)

        # ARIMA模型训练
        from statsmodels.tsa.stattools import adfuller
        adf_result = adfuller(daily_views)
        if adf_result[1] > 0.05:
            d = 1  # 非平稳数据，需一阶差分
        else:
            d = 0

        # 根据ACF/PACF选择 p=1, q=1
        model = ARIMA(daily_views, order=(1, d, 1))

        # 训练模型
        model_fit = model.fit()

        # 预测未来7天
        forecast = model_fit.forecast(steps=7)
        forecast_days = range(8, 15)

        # 生成图表
        plt.figure(figsize=(10, 6))
        plt.plot(daily_views.index, daily_views.values, 'bo-', label='历史热度')
        plt.plot(forecast_days, forecast, 'r--', marker='x', label='预测热度')
        plt.title(f'视频 {video_id} 热度预测（ARIMA模型）')
        plt.xlabel('天数 (1-7为历史，8-14为预测)')
        plt.ylabel('观看次数')
        plt.xticks(list(daily_views.index) + list(forecast_days))
        plt.legend()
        plt.grid(True)
        plot_path = 'data/heat_plot.png'
        plt.savefig(plot_path)
        plt.close()

        return {
            "history": daily_views.to_dict(),
            "forecast": forecast.tolist(),
            "plot_path": plot_path
        }

    except Exception as e:
        raise RuntimeError(f"预测失败: {str(e)}")