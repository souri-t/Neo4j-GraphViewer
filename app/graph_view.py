from __future__ import annotations

from html import escape
import json
from typing import Any, Dict

from pyvis.network import Network


GROUP_STYLE = {
    "Document": {"color": "#2563eb", "shape": "box"},
    "Chunk": {"color": "#16a34a", "shape": "dot"},
    "Similar Chunk": {"color": "#65a30d", "shape": "dot"},
    "NamedEntity": {"color": "#d97706", "shape": "diamond"},
    "JapaneseTerm": {"color": "#9333ea", "shape": "diamond"},
    "Topic": {"color": "#0891b2", "shape": "diamond"},
    "Entity": {"color": "#64748b", "shape": "diamond"},
}


def build_graph_html(graph_data: Dict[str, list[dict[str, Any]]], height: str = "620px") -> str:
    network = Network(height=height, width="100%", directed=True, bgcolor="#ffffff", font_color="#111827")
    network.barnes_hut(gravity=-32000, central_gravity=0.25, spring_length=180, spring_strength=0.03)

    for node in graph_data.get("nodes", []):
        group = node.get("group", "Entity")
        style = GROUP_STYLE.get(group, GROUP_STYLE["Entity"])
        title = build_node_title(node)
        network.add_node(
            node["id"],
            label=node.get("label", node["id"]),
            title=title,
            color=style["color"],
            shape=style["shape"],
        )

    for edge in graph_data.get("edges", []):
        network.add_edge(edge["from"], edge["to"], label=edge.get("label", ""), arrows="to")

    network.set_options(
        json.dumps(
            {
                "nodes": {
                    "borderWidth": 1,
                    "font": {"size": 15, "face": "Inter, system-ui, sans-serif"},
                },
                "edges": {
                    "color": {"color": "#94a3b8"},
                    "font": {"size": 11, "align": "middle"},
                    "smooth": {"type": "dynamic"},
                },
                "interaction": {
                    "hover": True,
                    "tooltipDelay": 120,
                    "navigationButtons": True,
                },
                "physics": {
                    "stabilization": {"iterations": 120},
                },
            }
        )
    )
    return network.generate_html(notebook=False)


def build_node_title(node: dict[str, Any]) -> str:
    parts = [f"<b>{escape(node.get('group', 'Node'))}</b>"]
    if node.get("path"):
        parts.append(escape(node["path"]))
    if node.get("text"):
        snippet = node["text"][:500]
        parts.append(f"<pre>{escape(snippet)}</pre>")
    return "<br>".join(parts)
