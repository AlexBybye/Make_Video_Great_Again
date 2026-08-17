# task3_predict_heat.py — 热度预测
# 使用自建 SegmentTree 做 O(log n) 区间和查询, 替代 pandas groupby O(n) 扫描
# 数据结构: SegmentTree (区间查询) + HashMap (O(1) 视频查询)

import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from scipy.signal import savgol_filter
from ds.data_store import DataStore
from ds.segment_tree import SegmentTree

# 暗色主题 + 中文字体
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'Heiti TC', 'STHeiti', 'Arial Unicode MS'],
    'axes.unicode_minus': False,
    'figure.facecolor': '#0D0D1A',
    'axes.facecolor': '#0D0D1A',
    'axes.edgecolor': '#333355',
    'axes.labelcolor': '#AAAACC',
    'text.color': '#DDDDEE',
    'xtick.color': '#8888AA',
    'ytick.color': '#8888AA',
    'grid.color': '#1E1E3A',
    'grid.alpha': 0.6,
    'legend.facecolor': '#12122A',
    'legend.edgecolor': '#333355',
    'legend.labelcolor': '#AAAACC',
})

ACCENT_PINK = '#FB7299'
ACCENT_CYAN = '#00D4AA'
ACCENT_GOLD = '#FFB347'
ACCENT_PURPLE = '#B07CEE'
ACCENT_WHITE = '#EEEEFF'


def predict_video_heat(video_id):
    try:
        t1 = time.time()
        store = DataStore()

        # HashMap O(1) 验证
        if not store.video_exists(video_id):
            raise ValueError("视频ID不存在")

        # 获取该视频的所有操作记录 (HashMap O(1))
        ops = store.get_video_operations(video_id)

        # 统计每日操作记录数，用于获取观看趋势分布
        daily_ops_arr = [0] * 31  # 索引0=day1, ...
        for op in ops:
            day = op['day']
            if 1 <= day <= 30:
                daily_ops_arr[day - 1] += 1

        # 按视频真实总观看量等比缩放，得到每日估算观看量
        video_info = store.get_video(video_id)
        actual_total_views = video_info['views'] if video_info else 0
        total_ops = sum(daily_ops_arr)
        if total_ops > 0 and actual_total_views > 0:
            scale = actual_total_views / total_ops
        else:
            scale = 1.0

        daily_counts_arr = [d * scale for d in daily_ops_arr]

        # 自建 SegmentTree — 支持 O(log n) 区间查询
        daily_tree = SegmentTree(daily_counts_arr)
        print(f"[Task3] 操作记录总数: {total_ops}, 视频真实观看量: {actual_total_views}, 缩放比例: {scale:.2f}")
        print(f"[Task3] SegmentTree 总观看量 (O(1)): {daily_tree.total_sum()}")
        print(f"[Task3] 前7天累计 (O(log n)): {daily_tree.query(0, 6)}")
        print(f"[Task3] 后7天累计 (O(log n)): {daily_tree.query(23, 29)}")

        # 确定有效数据长度
        daily_list = daily_counts_arr[:]
        non_zero_end = max((i for i, v in enumerate(daily_list) if v > 0), default=0)
        history_len = max(non_zero_end + 1, 10)
        daily_list = daily_list[:history_len]

        cumulative_views = list(np.cumsum(daily_list))

        # ARIMA 预测
        model = ARIMA(cumulative_views, order=(2, 1, 1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=7)
        forecast_days = range(history_len + 1, history_len + 8)
        forecast_vals = np.array(forecast)
        forecast = np.maximum.accumulate(np.maximum(forecast_vals, 0))

        # 平滑处理
        full_values = np.concatenate([cumulative_views, forecast])
        win = min(7, len(full_values) // 2) * 2 + 1
        if win >= 3:
            smoothed_values = savgol_filter(full_values, window_length=win, polyorder=2)
        else:
            smoothed_values = full_values

        # 绘图
        fig, ax = plt.subplots(figsize=(12, 6.5))
        fig.patch.set_facecolor('#0D0D1A')
        ax.set_facecolor('#0D0D1A')

        hist_idx = list(range(1, history_len + 1))
        all_idx = hist_idx + list(forecast_days)

        ax.bar(hist_idx, daily_list, color=ACCENT_CYAN, alpha=0.3,
               edgecolor=ACCENT_CYAN, linewidth=0.8, label='日新增观看')
        ax.plot(hist_idx, cumulative_views, color=ACCENT_PINK, linewidth=2.2,
                marker='o', markersize=4, label='累计观看(历史)')
        ax.plot(forecast_days, forecast, color=ACCENT_GOLD, linewidth=2.2,
                linestyle='--', marker='s', markersize=5, label='预测累计观看')
        ax.fill_between(forecast_days, forecast,
                         np.concatenate([cumulative_views[-1:], forecast[:-1]]),
                         color=ACCENT_GOLD, alpha=0.08)

        if len(smoothed_values) == len(all_idx):
            ax.plot(all_idx, smoothed_values, color=ACCENT_PURPLE, linewidth=1.2,
                    linestyle=':', alpha=0.7, label='平滑趋势')

        split_x = hist_idx[-1] + 0.5
        ax.axvline(x=split_x, color='#FFFFFF', alpha=0.15, linewidth=1, linestyle='-')

        ax.set_title(f'视频 #{video_id} 热度预测', fontsize=16, fontweight='bold',
                     color='#FFFFFF', pad=16)
        ax.set_xlabel('天数', fontsize=12, color='#AAAACC')
        ax.set_ylabel('观看次数', fontsize=12, color='#AAAACC')
        ax.set_xticks(all_idx)
        ax.set_xticklabels(all_idx, rotation=45, fontsize=8)
        ax.tick_params(colors='#8888AA')
        ax.legend(loc='upper left', framealpha=0.85, fontsize=10)
        ax.grid(True, alpha=0.3, linewidth=0.5)

        ax.annotate('预测区间', xy=(forecast_days[0], forecast[0]),
                    xytext=(forecast_days[0] - 3, forecast[0] * 1.15),
                    color=ACCENT_GOLD, fontsize=9,
                    arrowprops=dict(arrowstyle='->', color=ACCENT_GOLD, alpha=0.5))

        fig.tight_layout()
        plot_path = 'data/heat_plot.png'
        fig.savefig(plot_path, dpi=150, facecolor='#0D0D1A', bbox_inches='tight')
        plt.close(fig)

        t2 = time.time()
        print(f"task3耗时 (自建数据结构): {t2 - t1:.4f} 秒")

        daily_dict = {str(i + 1): int(v) for i, v in enumerate(daily_list)}
        cum_dict = {str(i + 1): int(v) for i, v in enumerate(cumulative_views)}

        return {
            "history": {"daily": daily_dict, "cumulative": cum_dict},
            "forecast": [float(x) for x in forecast],
            "forecast_days": [int(x) for x in forecast_days],
            "plot_path": plot_path
        }

    except Exception as e:
        raise RuntimeError(f"预测失败: {str(e)}")
