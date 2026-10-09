# 结构化思维 AI 助手 · 知识库 SKILL

一个可离线运行的本地语义知识库,把威克的结构化思维方法论(第一性原理 / MECE / 80/20 / 金字塔原理 / 价值模型 / 业务全景图)做成语义检索,供 AI 或人查询。

结构化思维不只用于产品管理,它是一套通用的「想清楚再发力」的方法,适用于产品、职业定位、创业、管理、人生选择等任何需要结构化决策的场景。

- **零 API key**:本地中文嵌入模型(BGE),clone 下来 `pip install` 即可用
- **双形态**:Obsidian 可读的 Markdown 笔记(人看)+ 向量索引(机器检索)
- **纯 Python**:嵌入 + 摄取 + 检索三件事,两个脚本搞定

## 内容来源

| 文档 | 类型 | 说明 |
| --- | --- | --- |
| 结构化产品思维.pdf | 讲义(24 页) | 完整方法论:思维方式、金字塔原理、第一性原理、MECE 五法、8020、3P 工具、四个案例、遍历场景法 |
| 使用结构化思维构建你的业务全景图.md | 公众号文章 | 结构化思维三板斧 + 信息屋 + 业务全景图构建 |
| 价值模型.md | 方法论源文档 | 聚焦第一性原理 → 找服务对象 → MECE 拆解 → 8020 找 20% 核心作 80% 突破点 |

## 快速开始

```bash
# 1. 安装依赖(首次运行会自动下载中文嵌入模型,约 90MB)
pip install -r requirements.txt

# 2. 摄取源文档 → 生成知识库 + 向量索引
python scripts/ingest.py

# 3. 语义检索
python scripts/query.py "MECE 有哪些分类方法" --top 5
python scripts/query.py "怎么找到自己的核心价值点" --top 5
```

## 项目结构

```
structured-thinking-ai-assistant/
├── SKILL.md                 # SKILL 定义(给 AI 的用法说明)
├── README.md                # 本文件
├── requirements.txt
├── sources/                 # 源文档(原始 PDF / MD)
├── scripts/
│   ├── embed.py             # 分块 + 嵌入的纯函数
│   ├── ingest.py            # 源文档 → Obsidian 笔记 + 向量索引
│   └── query.py             # 语义检索
└── knowledge/               # 生成的知识库
    ├── 结构化思维AI助手.md   # MOC 索引页
    ├── notes/               # 每篇笔记 = 一个语义块
    └── .vector/             # vectors.npy + meta.json
```

## 技术选型

- **嵌入模型**:`BAAI/bge-small-zh-v1.5`(fastembed 加载,512 维,中文语义效果好、体积小)
- **检索**:numpy 余弦相似度(数据量小时足够快,无需向量数据库)
- **存储**:Obsidian 知识库 = Markdown 笔记(frontmatter 带来源/标签)+ `.vector/` 索引

## 作为 SKILL 使用

将本仓库作为 SKILL 安装后,AI 会:

1. 识别到结构化思维相关问题时,先跑 `query.py` 做语义检索
2. 用召回段落作为事实依据组织答案,并标注来源

## 许可

MIT
