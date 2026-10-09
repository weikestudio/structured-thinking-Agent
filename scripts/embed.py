"""结构化产品思维知识库 —— 嵌入与分块工具。

提供两个可复用的纯函数：
- chunk_text: 把一段长文本按标题/空行切分成语义块
- embed_chunks: 用本地中文模型生成向量(512 维)

模型首次运行会自动下载到本地缓存(约 90MB)，之后离线可用。
"""

from __future__ import annotations

import hashlib
import re
from typing import Iterator

import numpy as np
from fastembed import TextEmbedding

# 本地中文嵌入模型(开源、离线可用、512 维)
MODEL_NAME = "BAAI/bge-small-zh-v1.5"

# 忽略 fastembed 的下载进度/日志噪音
import logging
logging.getLogger("fastembed").setLevel(logging.ERROR)


def chunk_id(text: str, source: str, idx: int) -> str:
    """为每个语义块生成稳定唯一 id(基于内容的 sha1 前 12 位 + 序号)。"""
    h = hashlib.sha1(f"{source}\n{idx}\n{text}".encode("utf-8")).hexdigest()[:12]
    return f"ch-{h}"


def normalize_ws(text: str) -> str:
    """把 PDF 抽取出的换行断句合并成可读段落。"""
    text = text.replace("　", " ")
    # 中文里单个换行通常只是排版换行，合并成连续文本
    text = re.sub(r"(?<=[一-鿿])\n(?=[一-鿿])", "", text)
    # 多个空行 → 段落分隔
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_into_chunks(text: str, source: str) -> list[dict]:
    """按空行/标题切分成语义块，过滤过短的噪音块。

    返回 [{"id", "text", "source", "index"}]
    """
    text = normalize_ws(text)
    # 以空行或 markdown 标题作为边界
    raw_parts = re.split(r"\n\s*\n|(?=^#{1,6}\s)", text, flags=re.MULTILINE)

    chunks: list[dict] = []
    idx = 0
    for part in raw_parts:
        part = part.strip()
        if len(part) < 6:  # 过滤封面/页码等噪音
            continue
        chunks.append({
            "id": chunk_id(part, source, idx),
            "text": part,
            "source": source,
            "index": idx,
        })
        idx += 1
    return chunks


def embed_chunks(chunks: list[dict], model_name: str = MODEL_NAME) -> np.ndarray:
    """对一批 chunk 生成向量，返回 (N, dim) 的 float32 矩阵。"""
    model = TextEmbedding(model_name=model_name)
    texts = [c["text"] for c in chunks]
    vecs = list(model.embed(texts))
    return np.asarray(vecs, dtype="float32")
