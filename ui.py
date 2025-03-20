# ui.py
# -*- coding: utf-8 -*-
import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import generate_videos
import generate_users_operations
import task1_similar_users
import task2_recommend_videos

class LoadingWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading")
        self.setFixedSize(700, 500)
        
        layout = QVBoxLayout()
        self.label = QLabel("Data is being generated, please wait...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.pixmap = QPixmap('resources/baisi.jpg').scaled(400, 400, 
                    Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label = QLabel()
        self.image_label.setPixmap(self.pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.image_label)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.worker = DataGenerator()
        self.worker.finished.connect(self.accept)
        self.worker.start()

class DataGenerator(QThread):
    finished = pyqtSignal()
    
    def run(self):
        generate_videos.generate_videos()
        generate_users_operations.generate_users_operations()
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Recommender System")
        self.setFixedSize(400, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        self.btn_task1 = QPushButton("Find Similar Users")
        self.btn_task2 = QPushButton("Featured Video")
        self.btn_quit = QPushButton("exit")
        
        layout.addWidget(self.btn_task1)
        layout.addWidget(self.btn_task2)
        layout.addSpacing(20)
        layout.addWidget(self.btn_quit)
        
        central_widget.setLayout(layout)
        
        self.btn_task1.clicked.connect(lambda: self.show_task_window(1))
        self.btn_task2.clicked.connect(lambda: self.show_task_window(2))
        self.btn_quit.clicked.connect(self.close)

    def show_task_window(self, task_num):
        self.task_window = TaskWindow(task_num)
        self.task_window.show()

class TaskWindow(QDialog):
    def __init__(self, task_num):
        super().__init__()
        self.task_num = task_num
        self.setWindowTitle(f"task{task_num}")
        self.setFixedSize(600, 400)
        
        layout = QVBoxLayout()
        self.input_label = QLabel("Please enter the user ID:")
        self.input_field = QLineEdit()
        self.btn_submit = QPushButton("execute")
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        
        layout.addWidget(self.input_label)
        layout.addWidget(self.input_field)
        layout.addWidget(self.btn_submit)
        layout.addWidget(self.result_area)
        
        self.btn_submit.clicked.connect(self.execute_task)
        self.setLayout(layout)

    def execute_task(self):
        user_id = self.input_field.text()
        if not user_id.isdigit():
            QMessageBox.warning(self, "error", "Please enter a valid numeric ID")
            return
            
        user_id = int(user_id)
        try:
            operations_df = pd.read_csv('data/operations.csv')
            existing_ids = operations_df['user_id'].unique()
            if user_id not in existing_ids:
                QMessageBox.warning(self, "error", "User ID does not exist")
                return
        except Exception as e:
            QMessageBox.critical(self, "error", str(e))
            return
            
        try:
            if self.task_num == 1:
                result = task1_similar_users.find_similar_users(user_id)
                self.display_task1(result)
            else:
                result = task2_recommend_videos.recommend_videos(user_id)
                self.display_task2(result)
        except Exception as e:
            QMessageBox.critical(self, "error", str(e))

    def display_task1(self, data):
        self.result_area.clear()
        self.result_area.append("user_ID | similarity")
        for item in data:
            self.result_area.append(f"{item['user_ID']} | {item['similarity']:.4f}")

    def display_task2(self, data):
        self.result_area.clear()
        self.result_area.append("Video_ID | label | Overall_rating")
        for item in data:
            self.result_area.append(f"{item['Video_ID']} | {item['label']} | {item['Overall_rating']:.2f}")

def run_app():
    app = QApplication(sys.argv)
    
    if not os.path.exists('data'):
        os.makedirs('data')
    
    loading = LoadingWindow()
    if loading.exec() == QDialog.DialogCode.Accepted:
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())