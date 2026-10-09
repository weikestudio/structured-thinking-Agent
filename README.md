# 结构化思维 Agent · 知识库 SKILL

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

## 安装

### 前置要求

- **Python 3.9+**(3.10 或更高版本最佳)
- 可联网的环境(仅首次安装依赖和下载嵌入模型时需要;之后完全离线)

### 第一步:克隆仓库

```bash
git clone https://github.com/weikestudio/structured-thinking-Agent.git
cd structured-thinking-Agent
```

### 第二步:安装依赖

建议用虚拟环境,避免污染系统 Python:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows 用 .venv\Scripts\activate
pip install -r requirements.txt
```

> 依赖极少:仅 `fastembed`(本地嵌入)、`numpy`、`pypdf`(解析 PDF)。安装后**不需要任何 API key**。

### 第三步:首次运行(自动下载中文模型)

首次运行 `ingest.py` 或 `query.py` 时,会自动从 HuggingFace 下载中文嵌入模型 `BAAI/bge-small-zh-v1.5`(约 90MB),缓存到本机。之后离线可用。

```bash
# 摄取源文档 → 生成知识库 + 向量索引
python scripts/ingest.py
```

> 如果下载慢,可设置 HF 镜像后再运行:
> ```bash
> export HF_ENDPOINT=https://hf-mirror.com   # 国内镜像加速
> python scripts/ingest.py
> ```

### 第四步:验证安装

```bash
python scripts/query.py "MECE 有哪些分类方法" --top 3
```

若能返回带 `score` 的相关笔记段落,即安装成功。

## 快速开始

```bash
# 语义检索(score 越高越相关)
python scripts/query.py "MECE 有哪些分类方法" --top 5
python scripts/query.py "怎么找到自己的核心价值点" --top 5
python scripts/query.py "接手一个新业务怎么快速上手" --top 5
```

## 项目结构

```
structured-thinking-Agent/
├── SKILL.md                 # SKILL 定义(给 AI 的用法说明)
├── README.md                # 本文件
├── LICENSE                  # MIT 许可证
├── requirements.txt
├── sources/                 # 源文档(原始 PDF / MD)
├── scripts/
│   ├── embed.py             # 分块 + 嵌入的纯函数
│   ├── ingest.py            # 源文档 → Obsidian 笔记 + 向量索引
│   └── query.py             # 语义检索
└── knowledge/               # 生成的知识库
    ├── 结构化思维Agent.md   # MOC 索引页(学习路径组织)
    ├── notes/               # 每篇笔记 = 一个语义块
    └── .vector/             # vectors.npy + meta.json
```

## 技术选型

- **嵌入模型**:`BAAI/bge-small-zh-v1.5`(fastembed 加载,512 维,中文语义效果好、体积小)
- **检索**:numpy 余弦相似度(数据量小时足够快,无需向量数据库)
- **存储**:Obsidian 知识库 = Markdown 笔记(frontmatter 带来源/标签)+ `.vector/` 索引

## 作为 SKILL 使用

### 方式一:Claude / 支持 SKILL 的 Agent 环境

将本仓库作为 SKILL 安装(目录内含 `SKILL.md`),安装后 AI 会:

1. 识别到结构化思维相关问题时,先跑 `query.py` 做语义检索
2. 用召回段落作为事实依据组织答案,并标注来源

`SKILL.md` 里的 `description` 是触发条件,`name: structured-thinking-agent` 是 SKILL 标识。

### 方式二:Obsidian 直接浏览

`knowledge/` 目录本身就是个迷你 Obsidian vault:

1. 在 Obsidian 里「打开文件夹作为仓库」,选中 `knowledge/`
2. 从入口 `结构化思维Agent.md`(MOC 索引页)开始,按学习路径七步浏览
3. 每篇笔记之间有 `[[双链]]`,点链接即可跳转

## 维护

源文档变更后,重新摄取:

```bash
python scripts/ingest.py
```

摄取流程:解析 `sources/` → 按语义分块 → 本地中文模型生成 512 维向量 → 写入笔记与索引。

## 许可

MIT
