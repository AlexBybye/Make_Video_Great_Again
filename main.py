import sys
import os
from PyQt6.QtWidgets import QApplication
from data_manager import DataManager
from ui import LoadingSplash, MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 确保目录存在
    os.makedirs("data", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    # 显示加载界面
    splash = LoadingSplash()
    DataManager()  # 初始化数据
    splash.close()

    # 显示主界面
    window = MainWindow()
    window.show()

    sys.exit(app.exec())