"""query.py —— 对知识库做语义检索(余弦相似度)。

用法:
    python scripts/query.py "你的问题"
    python scripts/query.py "MECE 有哪些分类方法" --top 5
    python scripts/query.py "怎么找服务对象" --tag 第一性原理   # 只检索某 Agent 领域的知识块

原理:
    把问题用同一个中文模型嵌入,再与 knowledge/.vector/vectors.npy 里的
    向量做余弦相似度,返回最相关的笔记段落。--tag 可限定只检索指定主题,
    用于多 Agent 架构下每个 Agent「聚焦核心能力」。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from embed import embed_chunks  # noqa: E402

VECTOR_DIR = ROOT / "knowledge" / ".vector"

# tag 中文别名 → 规范 tag,方便调用(对齐三 Agent 动词化命名)
TAG_ALIASES = {
    "本质": "第一性原理", "判断": "第一性原理", "essence": "第一性原理", "第一性": "第一性原理",
    "拆解": "MECE", "分解": "MECE", "decompose": "MECE", "分类": "MECE",
    "聚焦": "8020", "取舍": "8020", "focus": "8020", "80/20": "8020", "帕累托": "8020",
}


def normalize_tag(tag: str | None) -> str | None:
    if tag is None:
        return None
    return TAG_ALIASES.get(tag, tag)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype("float32"); b = b.astype("float32")
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def search(query: str, top_k: int = 5, tag: str | None = None) -> list[dict]:
    meta = json.loads((VECTOR_DIR / "meta.json").read_text(encoding="utf-8"))
    vectors = np.load(VECTOR_DIR / "vectors.npy")

    q_vec = embed_chunks([{"id": "q", "text": query, "source": "", "index": 0}])[0]

    scores = [cosine(q_vec, v) for v in vectors]
    order = np.argsort(scores)[::-1]

    results = []
    for i in order:
        c = meta["chunks"][i]
        if tag is not None and c["tag"] != tag:
            continue
        results.append({
            "score": round(scores[i], 4),
            "tag": c["tag"],
            "source": c["source"],
            "note": c["note"],
            "text": c["text"],
        })
        if len(results) >= top_k:
            break
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--tag", type=str, default=None,
                    help="只检索指定主题的知识块(支持别名:第一性原理/本质, MECE/拆解, 8020/聚焦)")
    args = ap.parse_args()

    tag = normalize_tag(args.tag)
    tag_hint = f" [tag:{tag}]" if tag else ""
    print(f"🔍 检索:「{args.query}」{tag_hint}\n")
    for r in search(args.query, args.top, tag):
        preview = r["text"].replace("\n", " ")[:80]
        print(f"  {r['score']:.3f}  [{r['tag']}] {r['source']} → {r['note']}")
        print(f"      {preview}\n")


if __name__ == "__main__":
    main()

