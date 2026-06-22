from __future__ import annotations

from html import escape
import json
from pathlib import PurePosixPath
from typing import Any

import numpy as np
from pyvis.network import Network


def build_virtual_graph(results: list[dict[str, Any]], similarity_threshold: float) -> dict[str, list[dict[str, Any]]]:
    nodes = []
    edges = []

    for row in results:
        metadata = row.get("metadata", {})
        nodes.append(
            {
                "id": row["id"],
                "label": build_node_label(metadata, row["id"]),
                "title": build_node_title(row),
            }
        )

    for left_index in range(len(results)):
        for right_index in range(left_index + 1, len(results)):
            left = results[left_index]
            right = results[right_index]
            similarity = cosine_similarity(left.get("embedding", []), right.get("embedding", []))
            if similarity >= similarity_threshold:
                edges.append(
                    {
                        "from": left["id"],
                        "to": right["id"],
                        "label": f"{similarity:.3f}",
                        "score": similarity,
                    }
                )

    return {"nodes": nodes, "edges": edges}


def build_graph_html(graph_data: dict[str, list[dict[str, Any]]], height: str = "620px") -> str:
    network = Network(height=height, width="100%", directed=False, bgcolor="#ffffff", font_color="#111827")
    network.barnes_hut(gravity=-22000, central_gravity=0.25, spring_length=190, spring_strength=0.035)

    for node in graph_data.get("nodes", []):
        network.add_node(
            node["id"],
            label=node.get("label", node["id"]),
            title=node.get("title", ""),
            color="#2563eb",
            shape="dot",
            size=18,
        )

    for edge in graph_data.get("edges", []):
        network.add_edge(
            edge["from"],
            edge["to"],
            label=edge.get("label", ""),
            title=f"cosine similarity: {edge.get('score', 0):.4f}",
            color="#94a3b8",
        )

    network.set_options(
        json.dumps(
            {
                "nodes": {
                    "borderWidth": 1,
                    "font": {"size": 14, "face": "Inter, system-ui, sans-serif"},
                },
                "edges": {
                    "font": {"size": 11, "align": "middle"},
                    "smooth": {"type": "dynamic"},
                },
                "interaction": {
                    "hover": True,
                    "dragNodes": False,
                    "tooltipDelay": 120,
                    "navigationButtons": True,
                },
                "physics": {
                    "stabilization": {"iterations": 140},
                },
            }
        )
    )
    return network.generate_html(notebook=False)


def build_node_title(row: dict[str, Any]) -> str:
    metadata = row.get("metadata", {})
    parts = [
        f"<b>{escape(str(metadata.get('title', 'Untitled')))}</b>",
        escape(str(metadata.get("path", ""))),
        f"Chunk: {escape(str(metadata.get('chunk_index', '')))}",
    ]
    document = row.get("document", "")
    if document:
        parts.append(f"<pre>{escape(document[:500])}</pre>")
    return "<br>".join(part for part in parts if part)


def build_node_label(metadata: dict[str, Any], fallback_id: str) -> str:
    path = str(metadata.get("path") or "")
    filename = PurePosixPath(path).name if path else ""
    label = filename or str(metadata.get("title") or fallback_id)
    chunk_index = metadata.get("chunk_index")
    if chunk_index is not None:
        return f"{label}\nChunk {chunk_index}"
    return label


def cosine_similarity(left: list[float], right: list[float]) -> float:
    left_vector = np.array(left, dtype=np.float32)
    right_vector = np.array(right, dtype=np.float32)
    if left_vector.size == 0 or right_vector.size == 0:
        return 0.0
    denominator = float(np.linalg.norm(left_vector) * np.linalg.norm(right_vector))
    if denominator == 0.0:
        return 0.0
    return float(np.dot(left_vector, right_vector) / denominator)
