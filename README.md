# Make Video Great Again

基于 Flask 的视频数据分析与推荐系统，数据结构课程大作业。

## 项目简介

本项目模拟多平台（抖音/TikTok/快手/X/Facebook）短视频推荐场景，从零构建数据结构层（HashMap、稀疏矩阵、堆、图、线段树、Trie、LRU），替代 scipy/pandas 等库的数据组织能力，并在此基础上实现相似用户查找、视频推荐、热度预测、用户聚类、视频聚类及强化学习推荐增强等分析任务，最终通过 Flask Web 界面交互式展示。

## 运行环境

- Python 3.9–3.12（推荐 3.12）
- 依赖包见 `requirements.txt`

## 快速开始

```bash
# 1. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
python3 app.py

# 4. 浏览器访问
# http://localhost:8080/
```

## 项目结构

```
Make_Video_Great_Again/
├── .gitignore                      # 本地环境与生成文件忽略规则
├── app.py                          # Flask Web 后端（端口8080）
├── database.py                     # SQLite 数据库初始化
├── data_manager.py                 # 数据导入管理
├── data_cache.py                   # 数据缓存层
├── requirements.txt                # Python 依赖
│
├── ds/                             # 自建数据结构层
│   ├── hash_map.py                 # HashMap — O(1) 键值查询
│   ├── sparse_matrix.py            # CSRSparseMatrix — 稀疏矩阵压缩存储
│   ├── max_heap.py                 # MaxHeap — Top-K 筛选
│   ├── segment_tree.py             # SegmentTree — O(log n) 区间和查询
│   ├── graph.py                    # Graph — BFS 路径回溯
│   ├── trie.py                     # Trie — 前缀搜索
│   ├── lru_cache.py                # LRUCache — 最近最少使用缓存
│   ├── bandit_store.py             # BanditDataStore — 强化学习数据结构
│   └── data_store.py               # DataStore — 统一数据入口
│
├── task1_similar_users.py          # 任务1：相似用户分析（稀疏矩阵+余弦相似度+Top-K）
├── task2_recommend_videos.py       # 任务2：视频推荐（图BFS协同过滤+推荐路径解释）
├── task3_predict_heat.py           # 任务3：热度预测（线段树+ARIMA时序预测）
├── task4_user_clustering.py        # 任务4：用户聚类（稀疏矩阵+PCA+MiniBatchKMeans）
├── task5_video_clustering.py       # 任务5：视频聚类（SVD降维+MiniBatchKMeans）
│
├── Alpha_embedding_Cluster.py      # 增强算法A：SVD Embedding 聚类推荐
├── Beta_Thompson_Sampling.py       # 增强算法B：Thompson Sampling 冷启动
├── Charlie_LinUCB.py               # 增强算法C：LinUCB 交互式反馈训练
│
├── crawl_real_data.py              # 真实数据爬取（B站API）
├── capture_videos.py               # 视频信息采集
├── capture_users_operation.py      # 用户行为数据采集
├── generate_videos.py              # 模拟视频生成
├── generate_users_operations.py    # 模拟用户与行为生成
├── test_performance.py             # 性能测试
│
├── data/                           # 本地生成的数据（不提交）
├── results/                        # Embedding 数据与可视化输出
└── web/                            # 前端
    ├── templates/index.html        # 主页模板
    ├── templates/test.html         # 测试页面
    └── static/
        ├── css/style.css           # 样式
        └── js/app.js               # 前端交互逻辑
```

## 功能模块

### 六个核心分析任务

| 任务 | 说明 | 核心数据结构 |
|------|------|-------------|
| Task1 相似用户 | 构建用户-标签稀疏矩阵，计算余弦相似度，Top-K 堆筛选 | CSRSparseMatrix + MaxHeap |
| Task2 视频推荐 | 基于图的 BFS 协同过滤，生成推荐路径解释 | Graph + HashMap + MaxHeap |
| Task3 热度预测 | 按天统计观看量，ARIMA 预测未来7天趋势 | SegmentTree |
| Task4 用户聚类 | 构建用户兴趣特征矩阵，PCA 降维 + MiniBatchKMeans | CSRSparseMatrix + HashMap |
| Task5 视频聚类 | 构建视频-用户稀疏矩阵，SVD 降维 + MiniBatchKMeans | HashMap + CSRSparseMatrix |
| Task6 推荐增强 | SVD Embedding、Thompson Sampling、LinUCB 交互训练 | BanditDataStore |

## 数据与生成文件

- `data/` 不提交到仓库；缺少 CSV 时，首次启动会自动生成模拟数据。
- 首次生成数据并构建自定义数据结构可能需要几分钟；需要保存聚类结果时会创建 `data/app.db`。
- SQLite 数据库、缓存、虚拟环境、日志和生成图片已通过 `.gitignore` 排除。
