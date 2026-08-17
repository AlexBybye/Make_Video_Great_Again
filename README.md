# Make Video Great Again 🎥

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.9.0-purple.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

</div>

## 📖 项目简介

Make Video Great Again 是一个基于人工智能的视频数据分析与推荐系统，本系统采用现代化的技术栈，结合 PyQt6 构建了直观的用户界面，实现了视频数据的智能分析与处理。

## ✨ 核心特性

- 🎯 **智能推荐引擎**
  - 基于协同过滤的个性化推荐
  - 深度学习模型支持(可以随时接入)
  - 实时推荐更新
  
- 📊 **高级数据分析**
  - 用户行为模式识别
  - 视频热度趋势预测
  - 多维度数据可视化
  
- 🔍 **智能聚类分析**
  - 用户群体智能划分
  - 视频内容自动分类
  - 特征工程优化
  - 聚类结果再度优化推荐

- 🎨 **现代化界面**
  - 响应式设计
  - 实时数据展示
  - 交互式操作体验

## 🛠️ 技术栈

- **核心框架**
  - Python 3.8+
  - PyQt6
  - scikit-learn
  - TensorFlow/PyTorch

- **数据处理**
  - pandas
  - numpy
  - scipy

- **可视化**
  - matplotlib
  - seaborn
  - plotly

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- CUDA 支持（可选，用于 GPU 加速）
- 8GB+ RAM
- 2GB+ 可用磁盘空间

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/AlexBybye/Make_Video_Great_Again.git
cd Make_Video_Great_Again
```

2. **创建虚拟环境**（推荐）
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动应用**
```bash
python main.py
```

## 📁 项目架构

```
Make_Video_Great_Again/
├── data/               # 数据存储与预处理（介于大小未储存云端）
├── results/            # 分析结果与可视化输出
├── resources/          # 静态资源与配置文件
├── ui.py               # 用户界面模块
│  
├──# 核心功能模块
│   ��── data_manager.py    # 数据管理
│   ├── data_cache.py      # 缓存系统
│   └── models/            # 机器学习模型(后续)
├──# 分析任务模块
│   ├── task1_similar_users.py
│   ├── task2_recommend_videos.py
│   ├── task3_predict_heat.py
│   ├── task4_user_clustering.py
│   └── task5_video_clustering.py
├──# 爬虫模块（B站数据）
│   ├── capture_users_operation.py
│   └── capture_videos.py        
├──# 新增聚类强化学习推荐模块
│   ├── Alpha_embedding_Cluster.py
│   ├── Beta_Thompson_Sampling.py
│   └── Charlie_LinUCB.py
├── test_performance.py               # 耗时计算模块
└── main.py            # 应用入口
```

## 🔬 功能模块详解

### 1. 智能推荐系统
- 基于协同过滤的个性化推荐
- 深度学习模型支持
- 实时推荐更新机制
- 多维度特征提取

### 2. 用户行为分析
- 行为模式识别
- 兴趣图谱构建
- 用户画像生成
- 群体特征分析

### 3. 视频内容分析
- 热度趋势预测
- 内容特征提取
- 自动分类标注
- 质量评估系统

### 4. 数据可视化
- 交互式图表
- 实时数据更新
- 多维度展示
- ���定义报表

## 🤝 贡献指南

我们欢迎各种形式的贡献，包括但不限于：

- 提交问题和建议
- 改进文档
- 提交代码改进
- 分享使用经验

## 📄 开源协议

本项目采用 MIT 协议开源，详情请查看 [LICENSE](LICENSE) 文件。

## 👥 开发团队

- **项目负责人**: AlexBybye
- **核心开发者**: 
AlexBybye BUSYING-1 happytzh
- **UI/UX 设计**: BUSYING-1 AlexBybye
- **强化学习等深度设计**: AlexBybye
## 📞 联系我们

- 项目主页：[GitHub](https://github.com/AlexBybye/Make_Video_Great_Again)


## 🌟 暴力测试（亿级数据：`50000users - 500000videos - 800-1200operations`）
- cpu: `i9-13900`
- 内存：`2048MB`  
- 测试结果：
```
| 步骤           | 耗时（秒）|
| -----------    | -------- |
| 生成数据        | 340.8385 |
| 加载数据        | 359.1548 |
| Task1 预模拟    | 7.3957   |
| Task1 模拟1     | 0.1570   |
| Task2 模拟      | 1.0478   |
| Task1 模拟2     | 0.1492   |
| Task3 模拟      | 10.0709  |
| Task4 模拟      | 20.7974  |
| Task5 模拟      | 14.4364  |
```
---

<div align="center">
  <sub>Built with ❤️ by AlexBybye and contributors.</sub>
</div> 
