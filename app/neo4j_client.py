import os
from typing import Any, Dict, Iterable, List

from neo4j import GraphDatabase


CHUNK_INDEX_NAME = "chunk_embedding_index"


class Neo4jClient:
    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self) -> None:
        self.driver.close()

    def verify(self) -> None:
        self.driver.verify_connectivity()

    def init_schema(self, embedding_dimension: int) -> None:
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")
            session.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE")
            session.run("CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
            session.run(
                f"""
                CREATE VECTOR INDEX {CHUNK_INDEX_NAME} IF NOT EXISTS
                FOR (c:Chunk) ON (c.embedding)
                OPTIONS {{
                  indexConfig: {{
                    `vector.dimensions`: {int(embedding_dimension)},
                    `vector.similarity_function`: 'cosine'
                  }}
                }}
                """
            )

    def clear_graph(self) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def upsert_document(self, document: Dict[str, Any], chunks: List[Dict[str, Any]]) -> None:
        with self.driver.session() as session:
            session.execute_write(self._upsert_document_tx, document, chunks)

    @staticmethod
    def _upsert_document_tx(tx, document: Dict[str, Any], chunks: List[Dict[str, Any]]) -> None:
        tx.run(
            """
            MERGE (d:Document {id: $id})
            SET d.title = $title,
                d.path = $path,
                d.text = $text
            """,
            **document,
        )
        for chunk in chunks:
            tx.run(
                """
                MATCH (d:Document {id: $document_id})
                MERGE (c:Chunk {id: $id})
                SET c.text = $text,
                    c.chunkIndex = $chunk_index,
                    c.embedding = $embedding
                MERGE (d)-[:HAS_CHUNK]->(c)
                """,
                document_id=document["id"],
                **chunk,
            )
            for entity in chunk.get("entities", []):
                tx.run(
                    """
                    MATCH (c:Chunk {id: $chunk_id})
                    MERGE (e:Entity {name: $name})
                    SET e.type = coalesce(e.type, $type)
                    MERGE (c)-[:MENTIONS]->(e)
                    """,
                    chunk_id=chunk["id"],
                    name=entity["name"],
                    type=entity["type"],
                )

    def create_chunk_similarities(self, pairs: Iterable[Dict[str, Any]]) -> None:
        rows = list(pairs)
        if not rows:
            return
        with self.driver.session() as session:
            session.run(
                """
                UNWIND $rows AS row
                MATCH (a:Chunk {id: row.source_id})
                MATCH (b:Chunk {id: row.target_id})
                MERGE (a)-[r:SIMILAR]->(b)
                SET r.score = row.score
                """,
                rows=rows,
            )

    def create_document_similarities(self, pairs: Iterable[Dict[str, Any]]) -> None:
        rows = list(pairs)
        if not rows:
            return
        with self.driver.session() as session:
            session.run(
                """
                UNWIND $rows AS row
                MATCH (a:Document {id: row.source_id})
                MATCH (b:Document {id: row.target_id})
                MERGE (a)-[r:SIMILAR]->(b)
                SET r.score = row.score
                """,
                rows=rows,
            )

    def search_chunks(self, embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                f"""
                CALL db.index.vector.queryNodes('{CHUNK_INDEX_NAME}', $limit, $embedding)
                YIELD node, score
                MATCH (d:Document)-[:HAS_CHUNK]->(node)
                RETURN
                  d.id AS document_id,
                  d.title AS title,
                  d.path AS path,
                  node.id AS chunk_id,
                  node.text AS text,
                  node.chunkIndex AS chunk_index,
                  score
                ORDER BY score DESC
                """,
                embedding=embedding,
                limit=limit,
            )
            return [dict(record) for record in result]

    def graph_context(self, chunk_id: str, similar_limit: int = 8) -> Dict[str, List[Dict[str, Any]]]:
        with self.driver.session() as session:
            center = session.run(
                """
                MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk {id: $chunk_id})
                RETURN c.id AS id, c.text AS text, c.chunkIndex AS chunk_index,
                       d.id AS document_id, d.title AS document_title, d.path AS document_path
                """,
                chunk_id=chunk_id,
            ).single()
            if center is None:
                return {"nodes": [], "edges": []}

            similar = session.run(
                """
                MATCH (center:Chunk {id: $chunk_id})-[r:SIMILAR]-(c:Chunk)
                MATCH (d:Document)-[:HAS_CHUNK]->(c)
                RETURN c.id AS id, c.text AS text, c.chunkIndex AS chunk_index,
                       d.id AS document_id, d.title AS document_title,
                       d.path AS document_path, r.score AS score
                ORDER BY r.score DESC
                LIMIT $limit
                """,
                chunk_id=chunk_id,
                limit=similar_limit,
            )
            entities = session.run(
                """
                MATCH (c:Chunk {id: $chunk_id})-[:MENTIONS]->(e:Entity)
                RETURN e.name AS name, e.type AS type
                ORDER BY e.name
                LIMIT 20
                """,
                chunk_id=chunk_id,
            )

            nodes: list[dict[str, Any]] = []
            edges: list[dict[str, Any]] = []

            center_row = dict(center)
            doc_id = center_row["document_id"]
            nodes.append({"id": doc_id, "label": center_row["document_title"], "group": "Document", "path": center_row["document_path"]})
            nodes.append({"id": chunk_id, "label": f"Chunk {center_row['chunk_index']}", "group": "Chunk", "text": center_row["text"]})
            edges.append({"from": doc_id, "to": chunk_id, "label": "HAS_CHUNK"})

            for row in similar:
                item = dict(row)
                if item["document_id"] not in {node["id"] for node in nodes}:
                    nodes.append(
                        {
                            "id": item["document_id"],
                            "label": item["document_title"],
                            "group": "Document",
                            "path": item["document_path"],
                        }
                    )
                nodes.append(
                    {
                        "id": item["id"],
                        "label": f"Chunk {item['chunk_index']}",
                        "group": "Similar Chunk",
                        "text": item["text"],
                    }
                )
                edges.append({"from": item["document_id"], "to": item["id"], "label": "HAS_CHUNK"})
                edges.append({"from": chunk_id, "to": item["id"], "label": f"SIMILAR {item['score']:.3f}"})

            for row in entities:
                item = dict(row)
                entity_id = f"entity:{item['name']}"
                nodes.append({"id": entity_id, "label": item["name"], "group": item["type"] or "Entity"})
                edges.append({"from": chunk_id, "to": entity_id, "label": "MENTIONS"})

            return {"nodes": _dedupe_nodes(nodes), "edges": edges}


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for node in nodes:
        if node["id"] in seen:
            continue
        seen.add(node["id"])
        unique.append(node)
    return unique
