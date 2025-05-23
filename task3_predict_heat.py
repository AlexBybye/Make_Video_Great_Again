# task3_predict_heat.py
# -*- coding: utf-8 -*-
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from scipy.signal import savgol_filter


plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体或其他支持中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


def predict_video_heat(video_id):
    """ 使用ARIMA模型预测视频热度 """
    try:
        t1 = time.time()
        # 读取数据
        ops_df = pd.read_csv('data/operations.csv')
        videos_df = pd.read_csv('data/videos.csv')

        # 验证视频是否存在
        if video_id not in videos_df['id'].values:
            raise ValueError("视频ID不存在")

        # 获取历史数据（按天统计）
        video_ops = ops_df[ops_df['video_id'] == video_id]
        daily_counts = video_ops.groupby('day').size().reindex(range(1, 8), fill_value=0)

        # 计算累计观看量（改为使用累计观看量作为时间序列数据）
        cumulative_views = daily_counts.cumsum()

        # ARIMA模型训练（强制一阶差分）
        model = ARIMA(cumulative_views, order=(1, 1, 0))  # 使用简单的AR(1)模型

        # 训练模型
        model_fit = model.fit()

        # 预测未来7天
        forecast = model_fit.forecast(steps=7)
        forecast_days = range(8, 15)

        # 强制预测值单调递增
        forecast = np.maximum.accumulate(forecast.values)

        # 绘制平滑曲线
        # 组合历史数据和预测数据
        full_values = np.concatenate([cumulative_views.values, forecast])
        smoothed_values = savgol_filter(full_values, window_length=5, polyorder=2)

        # 生成图表
        plt.figure(figsize=(10, 6))
        plt.plot(daily_counts.index, daily_counts.values, 'bo-', label='历史热度(日新增)')
        plt.plot(cumulative_views.index, cumulative_views.values, 'g-', label='历史热度(累计)')
        plt.plot(forecast_days, forecast, 'rx-', label='预测热度(累计)')
        plt.plot(range(1, 15), smoothed_values, 'b--', label='平滑曲线')
        plt.title(f'视频 {video_id} 热度预测（ARIMA模型改进版）')
        plt.xlabel('天数 (1-7为历史，8-14为预测)')
        plt.ylabel('观看次数')
        plt.xticks(list(daily_counts.index) + list(forecast_days))
        plt.legend()
        plt.grid(True)
        plot_path = 'data/heat_plot.png'
        plt.savefig(plot_path)
        plt.close()

        t2 = time.time()
        print(f"task3模拟耗时: {t2 - t1:.4f} 秒")

        return {
            "history": {
                "daily": daily_counts.to_dict(),
                "cumulative": cumulative_views.to_dict()
            },
            "forecast": forecast.tolist(),
            "plot_path": plot_path
        }

    except Exception as e:
        raise RuntimeError(f"预测失败: {str(e)}")