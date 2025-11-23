# ui.py - 界面模块
# -*- coding: utf-8 -*-
import os
import pandas as pd
import time
import numpy as np  # 模块二和模块三需要
import logging

# PyQt6 导入
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPixmap, QPainter, QPalette, QBrush, QIntValidator
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplashScreen, QLabel,
    QVBoxLayout, QWidget, QPushButton, QDialog,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QMessageBox, QHBoxLayout,
    QHeaderView
)

# 业务模块导入 (确保这些文件已存在且名称正确)
from data_manager import DataManager
from data_cache import DataCache
import task1_similar_users
import task2_recommend_videos
import task4_user_clustering
import task5_video_clustering

try:
    import Alpha_embedding_Cluster
    import Beta_Thompson_Sampling
    import Charlie_LinUCB
except ImportError as e:
    # 提醒用户，如果没有这些文件，相关功能将无法工作
    logging.error(f"无法导入进阶模块: {e}. 请确保文件名正确。")

logging.basicConfig(filename='results/ui_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# ==================== 加载闪屏 ====================
class LoadingSplash(QSplashScreen):
    """ 带进度提示的加载闪屏 """

    def __init__(self):
        # 加载并缩放图片
        pixmap = QPixmap("resources/preview.jpg").scaled(
            500, 500,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        super().__init__(pixmap)

        # 设置窗口属性
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background: transparent;")

        # 添加进度标签
        self.progress_label = QLabel("ciallo！正在生成数据哦~", self)
        self.progress_label.setGeometry(QRect(0, 450, 500, 30))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: white;
                font: bold 14px;
                background: rgba(0, 0, 0, 150);
                padding: 5px;
                border-radius: 8px;
            }
        """)

        # 显示并强制刷新界面
        self.show()
        QApplication.processEvents()


class BackgroundWidget(QWidget):
    """ 自定义背景部件 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_pixmap = QPixmap("resources/background.jpg")

    def paintEvent(self, event):
        """ 自动绘制背景 """
        painter = QPainter(self)
        # 保持比例并填充整个区域
        scaled_pixmap = self.bg_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(0, 0, scaled_pixmap)


# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    """ 系统主界面 """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能视频推荐系统")
        self.setFixedSize(1000, 800)
        self._init_ui()

    def _init_ui(self):
        """ 初始化界面组件 """
        # 创建带背景的中央部件
        central_widget = BackgroundWidget(self)
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)

        # 系统标题
        title_label = QLabel("视频推荐分析系统")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font: bold 32px;
                padding: 20px;
                background: rgba(255, 255, 255, 180);
                border-radius: 15px;
            }
        """)

        # 功能按钮样式
        button_style = """
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 15px;
                padding: 20px 40px;
                font: bold 18px;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                padding: 22px 42px;
            }
            QPushButton:pressed {
                background-color: #1c6da8;
            }
        """

        # 功能按钮
        self.btn_task1 = QPushButton("相似用户分析")
        self.btn_task2 = QPushButton("视频推荐")
        self.btn_task3 = QPushButton("热度预测")
        self.btn_task4 = QPushButton("用户聚类分析")
        self.btn_task5 = QPushButton("视频聚类分析")
        self.btn_task6 = QPushButton("推荐算法增强 (RL/冷启动)")  # <--- 新增
        self.btn_quit = QPushButton("退出系统")

        for btn in [self.btn_task1, self.btn_task2, self.btn_task3, self.btn_task4, self.btn_task5, self.btn_task6,
                    self.btn_quit]:  # <--- 修改
            btn.setStyleSheet(button_style)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # 按钮布局
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.btn_task1)
        button_layout.addWidget(self.btn_task2)
        button_layout.addWidget(self.btn_task3)
        button_layout.addWidget(self.btn_task4)
        button_layout.addWidget(self.btn_task5)
        button_layout.addWidget(self.btn_task6)  # <--- 新增
        button_layout.addWidget(self.btn_quit)
        button_layout.setSpacing(30)

        # 整合布局
        main_layout.addWidget(title_label)
        main_layout.addStretch(1)
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)

        # 连接信号
        self.btn_task1.clicked.connect(lambda: self._show_task_window(1))
        self.btn_task2.clicked.connect(lambda: self._show_task_window(2))
        self.btn_task3.clicked.connect(lambda: self._show_task_window(3))
        self.btn_task4.clicked.connect(lambda: self._show_task_window(4))
        self.btn_task5.clicked.connect(lambda: self._show_task_window(5))
        self.btn_task6.clicked.connect(lambda: self._show_task_window(6))  # <--- 新增
        self.btn_quit.clicked.connect(self.close)

    def _show_task_window(self, task_id):
        """ 显示任务窗口 """
        if task_id == 3:
            window = Task3Window(self)
        elif task_id == 4:
            window = Task4Window(self)
        elif task_id == 5:
            window = Task5Window(self)
        elif task_id == 6:  # <--- 新增 Task6Window 逻辑
            window = Task6Window(self)
        elif task_id in (1, 2):
            window = Task1_2Window(task_id, self)
        # 任务窗口的显示模式为非模态对话框
        window.show()


# ==================== 任务窗口 ====================
class Task1_2Window(QDialog):
    """ 任务分析窗口 """

    def __init__(self, task_id, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.data_mgr = DataManager()
        self._init_ui()

    def _init_ui(self):
        """ 初始化界面 """
        self.setWindowTitle(f"任务 {self.task_id} - {'相似用户分析' if self.task_id == 1 else '视频推荐'}")
        self.setFixedSize(800, 600)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # 输入区域
        input_layout = QHBoxLayout()
        lbl_user = QLabel("目标用户ID:")
        lbl_user.setStyleSheet("font: bold 16px; color: #2c3e50;")

        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("请输入用户ID...")
        self.input_user.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)

        input_layout.addStretch()
        input_layout.addWidget(lbl_user)
        input_layout.addWidget(self.input_user)
        input_layout.addStretch()

        # 执行按钮
        self.btn_execute = QPushButton("开始分析")
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 10px;
                padding: 12px 30px;
                font: bold 16px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219a52;
            }
        """)
        self.btn_execute.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_execute.clicked.connect(self._execute_task)

        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                padding: 5px;
                color: black;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                color: black;
            }
        """)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setSortingEnabled(True)

        # 初始化表格列
        if self.task_id == 1:
            headers = ["排名", "用户ID", "相似度"]
        else:
            headers = ["视频ID", "分类", "综合评分"]
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)
        self.result_table.setRowCount(0)  # 初始化为0行

        # 布局组织
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.btn_execute, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.result_table)

    def _execute_task(self):
        """ 执行分析任务 """
        try:
            # 获取并验证输入
            user_id = self.input_user.text().strip()
            if not user_id:
                self._show_error("请输入用户ID")
                return
            if not user_id.isdigit():
                self._show_error("用户ID必须为数字")
                return

            # 直接从数据源验证用户ID
            operations_df = DataCache.load_operations()
            if int(user_id) not in operations_df['user_id'].unique():
                self._show_error("用户ID不存在")
                return

            # 执行任务
            if self.task_id == 1:
                results = task1_similar_users.find_similar_users(int(user_id))
                headers = ["排名", "用户ID", "相似度"]
                data = [
                    (i + 1, row["user_ID"], f"{row['similarity']:.4f}")
                    for i, row in enumerate(results)
                ]
            else:
                results = task2_recommend_videos.recommend_videos(int(user_id))
                headers = ["视频ID", "分类", "综合评分"]
                data = [
                    (row["Video_ID"], row["label"], f"{row['Overall_rating']:.2f}")
                    for row in results
                ]

            # 显示结果
            self._display_results(headers, data)

        except Exception as e:
            logging.error(f"任务执行错误: {str(e)}", exc_info=True)  # 输出完整堆栈
            self._show_error(f"内部错误: {str(e)}")

    def _display_results(self, headers, data):
        """ 显示分析结果 """
        try:
            # 清空表格
            self.result_table.clear()
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(len(headers))
            self.result_table.setHorizontalHeaderLabels(headers)

            # 设置行数
            self.result_table.setRowCount(len(data))

            # 填充数据
            for row_idx, row_data in enumerate(data):
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setForeground(Qt.GlobalColor.black)  # 确保文字颜色为黑色
                    self.result_table.setItem(row_idx, col_idx, item)

            # 调整列宽
            self.result_table.resizeColumnsToContents()
            self.result_table.horizontalHeader().setStretchLastSection(True)

            # 强制刷新
            self.result_table.viewport().update()
            self.result_table.show()

            # 确保表格可见
            self.result_table.setVisible(True)

            # 记录日志
            logging.info(f"显示结果：{len(data)} 行数据")

        except Exception as e:
            logging.error(f"显示结果时发生错误: {str(e)}", exc_info=True)
            self._show_error(f"显示结果失败: {str(e)}")

    def _show_error(self, message):
        """ 显示错误提示 """
        QMessageBox.warning(
            self,
            "输入错误",
            message,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )


# 在Task3Window类前添加以下新类
class HeatPlotWindow(QDialog):
    """ 热度预测图表展示窗口 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("热度趋势预测图")
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.WindowType.Window)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 图片显示标签
        self.plot_label = QLabel()
        self.plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.plot_label)

        # 加载默认图片（如果有）
        self.load_image('data/heat_plot.png')

    def load_image(self, path):
        """ 加载并显示图片 """
        if os.path.exists(path):
            pixmap = QPixmap(path)
            pixmap = pixmap.scaled(self.size(),
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.plot_label.setPixmap(pixmap)
        else:
            self.plot_label.setText("图表生成失败")


# ==================== Task3Window 类 ====================
class Task3Window(QDialog):
    """ 视频热度预测窗口 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("视频热度预测")
        self.setFixedSize(800, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # 输入区域
        input_layout = QHBoxLayout()
        lbl_video = QLabel("目标视频ID:")
        lbl_video.setStyleSheet("font: bold 16px; color: #2c3e50;")

        self.input_video = QLineEdit()
        self.input_video.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 200px;
            }
        """)

        input_layout.addStretch()
        input_layout.addWidget(lbl_video)
        input_layout.addWidget(self.input_video)
        input_layout.addStretch()

        # 执行按钮
        self.btn_execute = QPushButton("开始预测")
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border-radius: 10px;
                padding: 12px 30px;
                font: bold 16px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.btn_execute.clicked.connect(self._execute_task)

        # 结果显示区域
        self.plot_label = QLabel()
        self.plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["天数", "预测观看量"])

        # 布局
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.btn_execute, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.plot_label)
        main_layout.addWidget(self.result_table)

    def _execute_task(self):
        """ 执行预测 """
        video_id = self.input_video.text().strip()
        videos_df = pd.read_csv('data/videos.csv')

        if not video_id.isdigit():
            self._show_error("请输入有效的数字ID")
            return
        if int(video_id) not in videos_df['id'].values:
            self._show_error("视频ID不存在")
            return

        try:
            from task3_predict_heat import predict_video_heat
            result = predict_video_heat(int(video_id))

            self.result_table.setColumnCount(2)
            self.result_table.setHorizontalHeaderLabels(["预测天数", "预计观看量"])
            self.result_table.setRowCount(7)
            for i, val in enumerate(result['forecast']):
                self.result_table.setItem(i, 0, QTableWidgetItem(f"第{i + 8}天"))
                self.result_table.setItem(i, 1, QTableWidgetItem(str(round(val, 2))))
            # 显示图表窗口
            self.plot_window = HeatPlotWindow()
            self.plot_window.load_image('data/heat_plot.png')
            self.plot_window.show()
        except Exception as e:
            self._show_error(str(e))

    def _show_error(self, msg):
        QMessageBox.critical(self, "错误", msg)


class Task4Window(QDialog):
    """用户聚类分析窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("用户聚类分析")
        self.setFixedSize(800, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # 聚类数量输入
        input_layout = QHBoxLayout()
        lbl_clusters = QLabel("聚类数量:")
        lbl_clusters.setStyleSheet("font: bold 16px; color: #2c3e50;")

        self.input_clusters = QLineEdit("10")
        self.input_clusters.setValidator(QIntValidator(2, 20))
        self.input_clusters.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 100px;
            }
        """)

        input_layout.addStretch()
        input_layout.addWidget(lbl_clusters)
        input_layout.addWidget(self.input_clusters)
        input_layout.addStretch()

        # 执行按钮
        self.btn_execute = QPushButton("开始聚类分析")
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                border-radius: 10px;
                padding: 12px 30px;
                font: bold 16px;
            }
            QPushButton:hover { background-color: #1abc9c; }
        """)
        self.btn_execute.clicked.connect(self._execute_task)

        # 结果显示区域
        self.plot_label = QLabel()
        self.plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["用户ID", "年龄", "聚类"])

        # 布局
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.btn_execute, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.plot_label)
        main_layout.addWidget(self.result_table)

    def _execute_task(self):
        """执行聚类分析"""
        try:
            n_clusters = int(self.input_clusters.text())
            if n_clusters < 2 or n_clusters > 20:
                raise ValueError("聚类数量应在2-20之间")

            result = task4_user_clustering.cluster_users(n_clusters=n_clusters)

            # 显示图表
            self.plot_window = HeatPlotWindow()
            self.plot_window.load_image(result['plot_path'])
            self.plot_window.show()

            # 显示数据
            self._display_results(result['data'])

        except Exception as e:
            self._show_error(str(e))

    def _display_results(self, data):
        """显示聚类结果"""
        self.result_table.clear()
        self.result_table.setRowCount(len(data))
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["用户ID", "年龄", "聚类"])

        for row_idx, row in enumerate(data):
            self.result_table.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
            self.result_table.setItem(row_idx, 1, QTableWidgetItem(str(row['age'])))
            self.result_table.setItem(row_idx, 2, QTableWidgetItem(str(row['cluster'])))

        self.result_table.resizeColumnsToContents()

    def _show_error(self, msg):
        QMessageBox.critical(self, "错误", msg)


class Task5Window(QDialog):
    """视频聚类分析窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("视频聚类分析")
        self.setFixedSize(800, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # 聚类数量输入
        input_layout = QHBoxLayout()
        lbl_clusters = QLabel("聚类数量:")
        lbl_clusters.setStyleSheet("font: bold 16px; color: #2c3e50;")

        self.input_clusters = QLineEdit("5")
        self.input_clusters.setValidator(QIntValidator(2, 20))
        self.input_clusters.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 100px;
            }
        """)

        input_layout.addStretch()
        input_layout.addWidget(lbl_clusters)
        input_layout.addWidget(self.input_clusters)
        input_layout.addStretch()

        # 执行按钮
        self.btn_execute = QPushButton("开始聚类分析")
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border-radius: 10px;
                padding: 12px 30px;
                font: bold 16px;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        self.btn_execute.clicked.connect(self._execute_task)

        # 结果显示区域
        self.plot_label = QLabel()
        self.plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["视频ID", "分类", "观看数", "点赞数", "聚类"])

        # 布局
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.btn_execute, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.plot_label)
        main_layout.addWidget(self.result_table)

    def _execute_task(self):
        """执行聚类分析"""
        try:
            n_clusters = int(self.input_clusters.text())
            if n_clusters < 2 or n_clusters > 20:
                raise ValueError("聚类数量应在2-20之间")

            result = task5_video_clustering.cluster_videos(n_clusters=n_clusters)

            # 显示图表
            self.plot_window = HeatPlotWindow()
            self.plot_window.load_image(result['plot_path'])
            self.plot_window.show()

            # 显示数据
            self._display_results(result['data'])

        except Exception as e:
            self._show_error(str(e))

    def _display_results(self, data):
        """显示聚类结果"""
        self.result_table.clear()
        self.result_table.setRowCount(len(data))
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["视频ID", "分类", "观看数", "点赞数", "聚类"])

        for row_idx, row in enumerate(data):
            self.result_table.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
            self.result_table.setItem(row_idx, 1, QTableWidgetItem(row['tag']))
            self.result_table.setItem(row_idx, 2, QTableWidgetItem(str(row['views'])))
            self.result_table.setItem(row_idx, 3, QTableWidgetItem(str(row['likes'])))
            self.result_table.setItem(row_idx, 4, QTableWidgetItem(str(row['cluster'])))

        self.result_table.resizeColumnsToContents()

    def _show_error(self, msg):
        QMessageBox.critical(self, "错误", msg)


# ==================== 新增 Task6Window 类 (进阶算法增强) ====================
class Task6Window(QDialog):
    """推荐算法增强（Embedding/TS/RL）窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.embedding_dim = 20  # 默认 Embedding 维度
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("推荐算法进阶增强")
        self.setFixedSize(900, 650)  # 稍大一点

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # 标题
        title_label = QLabel("三大推荐算法增强模块 (RL/冷启动)")
        title_label.setStyleSheet("font: bold 20px; color: #2c3e50; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # ----------------- 模块参数/操作区 -----------------
        param_layout = QHBoxLayout()
        lbl_dim = QLabel("Embedding 维度:")
        self.input_dim = QLineEdit(str(self.embedding_dim))
        self.input_dim.setValidator(QIntValidator(10, 50))
        self.input_dim.setFixedWidth(50)

        param_layout.addStretch()
        param_layout.addWidget(lbl_dim)
        param_layout.addWidget(self.input_dim)
        param_layout.addStretch()

        main_layout.addLayout(param_layout)

        module_layout = QHBoxLayout()

        # 1. 聚类 -> 向量 (Embedding)
        self.btn_embed = self._create_module_button("1. 生成簇 Embedding (SVD)", "#3498db")
        self.btn_embed.clicked.connect(self._execute_embedding)

        # 2. 冷启动 (Thompson Sampling)
        self.btn_ts = self._create_module_button("2. 模拟冷启动 (TS)", "#f39c12")
        self.btn_ts.clicked.connect(self._simulate_ts)

        # 3. 实时反馈 (LinUCB RL)
        self.btn_rl = self._create_module_button("3. 模拟实时反馈 (LinUCB)", "#e74c3c")
        self.btn_rl.clicked.connect(self._simulate_rl)

        module_layout.addWidget(self.btn_embed)
        module_layout.addWidget(self.btn_ts)
        module_layout.addWidget(self.btn_rl)

        main_layout.addLayout(module_layout)

        # ----------------- 结果显示区 -----------------

        self.status_label = QLabel("状态：请先运行 Task 4/5 聚类。")
        self.status_label.setStyleSheet(
            "font: 14px; color: #2c3e50; padding: 10px; border: 1px dashed #bdc3c7; border-radius: 5px;")
        main_layout.addWidget(self.status_label)

        # 详细输出表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["模块", "关键参数", "运行结果", "耗时"])
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setRowCount(0)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.result_table.horizontalHeader().setStretchLastSection(True)

        main_layout.addWidget(self.result_table)

    def _create_module_button(self, text, color):
        """创建统一风格的按钮"""
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 15px;
                font: bold 14px;
                min-height: 50px;
            }}
            QPushButton:hover {{
                background-color: rgba(46, 204, 113, 0.9); /* 调整悬停颜色 */
                background-color: {color};
            }}
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _execute_embedding(self):
        """执行模块一：SVD Embedding"""
        try:
            self.embedding_dim = int(self.input_dim.text())
            self.status_label.setText("状态：正在运行 SVD 簇 Embedding 生成...")
            QApplication.processEvents()

            # 依赖检查
            if not os.path.exists('data/users_clustered.csv') or not os.path.exists('data/videos_clustered.csv'):
                QMessageBox.warning(self, "依赖缺失",
                                    "请先运行 '用户聚类分析' 和 '视频聚类分析' (Task4/5) 确保生成聚类文件！")
                self.status_label.setText("状态：依赖缺失，Embedding 失败。")
                return

            # 核心调用
            start_time = time.time()
            result = Alpha_embedding_Cluster.get_cluster_embeddings(embedding_dim=self.embedding_dim)
            end_time = time.time()
            runtime = end_time - start_time

            # 检查是否有错误
            if "error" in result:
                raise RuntimeError(result["error"])

            # 显示结果
            self.status_label.setText(result.get("message", "SVD Embedding 运行完成。"))
            self._add_result_row(
                "SVD Embedding (Alpha)",
                f"Dim={self.embedding_dim}",
                f"U:{result['user_embeddings_shape']} V:{result['video_embeddings_shape']}",
                f"{runtime:.2f} s"
            )

        except Exception as e:
            self._show_error(f"SVD Embedding 失败: {str(e)}")
            self.status_label.setText("状态：SVD Embedding 失败。")
            logging.error(f"SVD Embedding 失败: {str(e)}")

    def _simulate_ts(self):
        """模拟执行模块二：Thompson Sampling"""
        try:
            self.status_label.setText("状态：正在运行 Thompson Sampling 冷启动模拟 (50轮迭代)...")  # <--- 修改这里的文字提示
            QApplication.processEvents()

            start_time = time.time()

            # 核心调用
            # 确保这里的 ranker.ColdStartRanker 的 __init__ 已经修改为 initial_alpha=1, initial_beta=1
            ranker = Beta_Thompson_Sampling.ColdStartRanker(initial_alpha=1, initial_beta=1, threshold_N=20)
            new_clusters = [1, 5, 8]  # 模拟新簇 ID

            NUM_ITERATIONS = 50  # <--- 将迭代次数增加到 50 轮

            for i in range(NUM_ITERATIONS):
                ranking = ranker.simulate_ranking(new_clusters)
                top_cluster = ranking[0][0]
                # 模拟簇 5 表现好 (0.7)，簇 8 表现差 (0.3)
                is_pos = np.random.rand() < (0.7 if top_cluster == 5 else (0.3 if top_cluster == 8 else 0.5))
                ranker.update_feedback(top_cluster, is_pos)

            end_time = time.time()
            runtime = end_time - start_time

            # 获取最终状态
            final_metrics_5 = ranker._get_metrics(5)  # 检查表现好的簇 5
            avg_ctr_5 = final_metrics_5['alpha'] / (final_metrics_5['alpha'] + final_metrics_5['beta'])

            final_metrics_8 = ranker._get_metrics(8)  # 检查表现差的簇 8
            avg_ctr_8 = final_metrics_8['alpha'] / (final_metrics_8['alpha'] + final_metrics_8['beta'])

            self.status_label.setText(f"TS 模拟完成。簇5估计CTR={avg_ctr_5:.4f} > 簇8={avg_ctr_8:.4f}")
            self._add_result_row(
                "TS 冷启动 (Beta)",
                f"50轮迭代",
                f"簇5/8 CTR: {avg_ctr_5:.4f}/{avg_ctr_8:.4f}",
                f"{runtime:.2f} s"
            )

        except Exception as e:
            self._show_error(f"Thompson Sampling 失败: {str(e)}")
            self.status_label.setText("状态：TS 模拟失败。")
            logging.error(f"Thompson Sampling 失败: {str(e)}")

    def _simulate_rl(self):
        """模拟执行模块三：LinUCB RL"""
        try:
            self.embedding_dim = int(self.input_dim.text())
            self.status_label.setText("状态：正在运行 LinUCB RL 实时反馈模拟 (5轮迭代)...")
            QApplication.processEvents()

            # 依赖检查：需要 Embedding 文件存在
            if not os.path.exists('results/user_cluster_embeddings.csv'):
                QMessageBox.warning(self, "依赖缺失", "请先运行 '生成簇 Embedding' 确保生成 Embedding 文件！")
                self.status_label.setText("状态：依赖缺失，LinUCB 失败。")
                return

            start_time = time.time()

            # 核心调用（使用演示逻辑）
            bandit = Charlie_LinUCB.LinUCBBandit(alpha=0.2, embedding_dim=self.embedding_dim)

            user_id = 1
            arm_A = 1  # 高奖励臂
            arm_B = 4  # 低奖励臂

            for i in range(5):
                ucb_A = bandit.get_ucb_score(user_id, arm_A)
                ucb_B = bandit.get_ucb_score(user_id, arm_B)
                chosen_arm = arm_A if ucb_A >= ucb_B else arm_B
                reward = 0.8 if chosen_arm == arm_A else 0.2
                bandit.update_feedback(user_id, chosen_arm, reward)

            end_time = time.time()
            runtime = end_time - start_time

            final_ucb_A = bandit.get_ucb_score(user_id, arm_A)
            final_ucb_B = bandit.get_ucb_score(user_id, arm_B)

            self.status_label.setText(f"LinUCB 模拟完成。UCB(A)={final_ucb_A:.4f} > UCB(B)={final_ucb_B:.4f}")
            self._add_result_row(
                "LinUCB RL (Charlie)",
                f"Alpha=0.2, Dim={self.embedding_dim}",
                f"UCB A/B: {final_ucb_A:.4f}/{final_ucb_B:.4f}",
                f"{runtime:.2f} s"
            )

        except Exception as e:
            self._show_error(f"LinUCB 失败: {str(e)}")
            self.status_label.setText("状态：LinUCB 模拟失败。")
            logging.error(f"LinUCB 失败: {str(e)}")

    def _add_result_row(self, module, params, result, runtime):
        """向结果表格添加一行数据"""
        row_count = self.result_table.rowCount()
        self.result_table.insertRow(row_count)

        data = [module, params, result, runtime]

        for col_idx, cell_data in enumerate(data):
            item = QTableWidgetItem(str(cell_data))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_table.setItem(row_count, col_idx, item)

        self.result_table.resizeColumnsToContents()
        self.result_table.horizontalHeader().setStretchLastSection(True)

    def _show_error(self, msg):
        """ 显示错误提示 """
        QMessageBox.critical(self, "错误", msg)


if __name__ == "__main__":
    # 模块测试代码
    app = QApplication([])
    window = MainWindow()  # 使用 MainWindow 启动，方便测试所有任务
    window.show()
    app.exec()