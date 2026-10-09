"""ingest.py —— 把 sources/ 下的源文档摄取为 Obsidian 知识库 + 向量索引。

用法:
    python scripts/ingest.py

产物:
    knowledge/            —— Obsidian 笔记(每篇 = 一个语义块,frontmatter 含来源/标签)
    knowledge/结构化产品思维.md —— MOC 总索引页(人在 Obsidian 里浏览用)
    knowledge/.vector/    —— 向量索引(vectors.npz + meta.json),供 query.py 检索
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

# 让脚本可从任意 cwd 运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from embed import embed_chunks, split_into_chunks  # noqa: E402

SOURCES_DIR = ROOT / "sources"
KNOWLEDGE_DIR = ROOT / "knowledge"
NOTES_DIR = KNOWLEDGE_DIR / "notes"
VECTOR_DIR = KNOWLEDGE_DIR / ".vector"

# 主题标签体系(按关键词启发式归类,fallback 到「结构化思维」)
TAGS = [
    ("价值模型", ["价值模型", "服务对象", "价值点", "突破点", "80%", "价值全景图", "杠杆", "舍九取一", "主服务对象", "次生对象"]),
    ("第一性原理", ["第一性原理", "以终为始", "3P", "Pupose", "顶层设计", "本质"]),
    ("MECE", ["MECE", "彼此独立", "完全穷尽", "二分法", "过程法", "要素法", "公式法", "矩阵法", "分类"]),
    ("8020", ["8020", "80/20", "聚焦", "关键路径", "20%"]),
    ("金字塔原理", ["金字塔", "结论先行", "归因模型", "自下而上", "自上而下"]),
    ("工具方法", ["遍历场景", "信息屋", "结构图", "归纳问题", "形成框架"]),
    ("案例", ["Case", "案例", "PPT", "711", "购物袋", "营销", "全景图"]),
    ("思维之美", ["四剑客", "茶如人生", "对君酌", "晨雪", "圣人", "大脑", "天赋"]),
]


def classify(text: str, source: str = "") -> str:
    # 来源优先:价值模型.md 的内容统一归「价值模型」,避免被三板斧关键词拆散到学习路径前几步
    if source == "价值模型":
        return "价值模型"
    for tag, kws in TAGS:
        for kw in kws:
            if kw in text:
                return tag
    return "结构化思维"


def parse_md(path: Path) -> tuple[str, str]:
    """读取 markdown 源文档,剥离 YAML frontmatter,返回 (title, body)。"""
    raw = path.read_text(encoding="utf-8")
    title = path.stem
    body = raw
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, flags=re.DOTALL)
    if m:
        fm, body = m.group(1), m.group(2)
        for line in fm.splitlines():
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"').strip("'")
    return title, body


def parse_pdf(path: Path) -> str:
    """提取 PDF 全文(逐页),过滤纯图片无文字页。"""
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages):
        t = (page.extract_text() or "").strip()
        if t:
            pages.append(f"<!-- 第 {i + 1} 页 -->\n{t}")
    return "\n\n".join(pages)


def slugify(text: str, maxlen: int = 28) -> str:
    s = re.sub(r"[^\w一-鿿-]+", "-", text).strip("-")
    return s[:maxlen] or "note"


def build_note(chunk: dict, title: str) -> str:
    """生成一篇 Obsidian 笔记的 markdown 文本。"""
    tag = classify(chunk["text"], chunk["source"])
    safe_title = slugify(title)
    note_title = f"{tag}·{safe_title}·{chunk['id']}"
    return (
        "---\n"
        f"id: {chunk['id']}\n"
        f"source: \"{chunk['source']}\"\n"
        f"index: {chunk['index']}\n"
        f"tags: [\"结构化思维Agent\", \"{tag}\"]\n"
        "---\n\n"
        f"# {note_title}\n\n"
        f"> 来源:[[{chunk['source']}]] · 分块 {chunk['index']}\n\n"
        f"{chunk['text']}\n"
    )


def main() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks: list[dict] = []
    sources_index: list[dict] = []

    for path in sorted(SOURCES_DIR.iterdir()):
        if path.suffix.lower() == ".md":
            title, body = parse_md(path)
            text = body
        elif path.suffix.lower() == ".pdf":
            title = path.stem
            text = parse_pdf(path)
        else:
            continue

        print(f"[ingest] 解析 {path.name} ...")
        chunks = split_into_chunks(text, source=title)
        print(f"          → {len(chunks)} 个语义块")
        all_chunks.extend(chunks)
        sources_index.append({"source": title, "file": path.name, "chunks": len(chunks)})

    if not all_chunks:
        print("[ingest] 未找到可摄取的内容,退出。")
        return

    print(f"[ingest] 生成嵌入(共 {len(all_chunks)} 块)...")
    vectors = embed_chunks(all_chunks)
    print(f"[ingest] 嵌入完成,形状 {vectors.shape}")

    # 写入笔记 + meta
    meta: list[dict] = []
    for chunk, vec in zip(all_chunks, vectors):
        note_path = NOTES_DIR / f"{chunk['id']}.md"
        note_path.write_text(build_note(chunk, chunk["source"]), encoding="utf-8")
        meta.append({
            "id": chunk["id"],
            "text": chunk["text"],
            "source": chunk["source"],
            "index": chunk["index"],
            "tag": classify(chunk["text"], chunk["source"]),
            "note": f"notes/{chunk['id']}.md",
        })

    # 向量 + meta 落盘
    np.save(VECTOR_DIR / "vectors.npy", vectors)
    (VECTOR_DIR / "meta.json").write_text(
        json.dumps({"model": "BAAI/bge-small-zh-v1.5", "dim": int(vectors.shape[1]),
                    "chunks": meta, "sources": sources_index},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 写 MOC 索引页
    write_moc(meta, sources_index)

    print(f"[ingest] 完成: {len(all_chunks)} 篇笔记 → {NOTES_DIR}")
    print(f"[ingest] 向量索引 → {VECTOR_DIR}")


def first_text_line(text: str, maxlen: int = 40) -> str:
    """取第一条非 HTML 注释、非空的有效行作为预览标题。"""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("<!--"):
            continue
        return line[:maxlen]
    return "(空)"


def write_moc(meta: list[dict], sources: list[dict]) -> None:
    LEARNING_PATH = [
        ("第一步 · 理解结构化思维", ["结构化思维"], "什么是结构化思维,它与惯性/直觉/水平/逻辑思维有何不同"),
        ("第二步 · 以终为始(第一性原理)", ["第一性原理"], "从本质出发,先想清楚目的与价值(3P 工具、顶层设计)"),
        ("第三步 · MECE(不重不漏)", ["MECE"], "彼此独立、完全穷尽;五种分类法;主观 vs 客观分类"),
        ("第四步 · 8020(聚焦核心)", ["8020"], "舍九取一,找到 20% 核心作为 80% 工作的突破点"),
        ("第五步 · 价值模型(三板斧落地)", ["价值模型"], "聚焦第一性原理→找服务对象→拆解价值点→找 20% 核心作 80% 突破点"),
        ("第六步 · 工具与案例", ["工具方法", "案例", "金字塔原理"], "遍历场景法、信息屋、金字塔原理、业务全景图与实战案例"),
        ("第七步 · 思维之美", ["思维之美"], "结构化思维的审美与体悟"),
    ]

    lines = [
        "---",
        "tags: [结构化思维Agent, MOC]",
        "---",
        "",
        "# 结构化思维 Agent · 知识库索引",
        "",
        "> 由 `scripts/ingest.py` 自动生成。人浏览入口;机器检索走 `.vector/` 向量索引。",
        "",
        "## 学习路径",
        "",
        "结构化思维三步走:先**理解**什么是结构化思维,再掌握**三板斧**(以终为始 / MECE / 8020),最后用**价值模型**把三板斧落地到「我该把力气花在哪」,并辅以工具与案例。",
        "",
    ]
    for title, tags, desc in LEARNING_PATH:
        items = [m for m in meta if m["tag"] in tags]
        if not items:
            continue
        lines.append(f"## {title}")
        lines.append(f"")
        lines.append(f"> {desc}")
        lines.append("")
        for m in items:
            preview = first_text_line(m["text"])
            lines.append(f"- [[{m['id']}]] {preview}")
        lines.append("")

    lines += ["## 源文档", ""]
    for s in sources:
        lines.append(f"- **{s['source']}**(`{s['file']}`,{s['chunks']} 块)")

    (KNOWLEDGE_DIR / "结构化思维Agent.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
