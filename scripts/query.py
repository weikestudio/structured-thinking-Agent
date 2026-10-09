"""query.py —— 对知识库做语义检索(余弦相似度)。

用法:
    python scripts/query.py "你的问题"
    python scripts/query.py "MECE 有哪些分类方法" --top 5

原理:
    把问题用同一个中文模型嵌入,再与 knowledge/.vector/vectors.npy 里的
    向量做余弦相似度,返回最相关的笔记段落。
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


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype("float32"); b = b.astype("float32")
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def search(query: str, top_k: int = 5) -> list[dict]:
    meta = json.loads((VECTOR_DIR / "meta.json").read_text(encoding="utf-8"))
    vectors = np.load(VECTOR_DIR / "vectors.npy")

    q_vec = embed_chunks([{"id": "q", "text": query, "source": "", "index": 0}])[0]

    scores = [cosine(q_vec, v) for v in vectors]
    order = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in order:
        c = meta["chunks"][i]
        results.append({
            "score": round(scores[i], 4),
            "tag": c["tag"],
            "source": c["source"],
            "note": c["note"],
            "text": c["text"],
        })
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    print(f"🔍 检索:「{args.query}」\n")
    for r in search(args.query, args.top):
        preview = r["text"].replace("\n", " ")[:80]
        print(f"  {r['score']:.3f}  [{r['tag']}] {r['source']} → {r['note']}")
        print(f"      {preview}\n")


if __name__ == "__main__":
    main()
