import os
import csv
import httpx

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, PointStruct


from settings import settings


class RetrievalManager:
    def __init__(self):
        self.qdrant_client = QdrantClient(url=settings.qdrant.URL)
        self.collection_name = settings.qdrant.QA_COLLECTION_NAME
        self.vector_size = 768  # Adjust if needed
        self.distance = "Cosine"  # Adjust if needed
        self.top_n = settings.qdrant.TOP_N
        self.fill_collection_if_needed()

    def _collection_has_data(self) -> bool:
        try:
            info = self.qdrant_client.get_collection(self.collection_name)
            return info.points_count > 0
        except Exception:
            return False

    def _create_collection(self):
        self.qdrant_client.create_collection(
            self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=self.distance,
            ),
        )

    def _embed(self, text: str) -> list[float]:
        embedder_endpoint = f"{settings.embedder.API_BASE_URL}/embeddings"
        headers = {"Content-Type": "application/json"}
        data = {"model": settings.embedder.MODEL_NAME, "input": [text]}
        with httpx.Client() as client:
            response = client.post(embedder_endpoint, headers=headers, json=data)
            raw = response.json()
            if response.status_code == 200:
                return raw.get("data", [])[0].get("embedding", [])
            raise Exception(f"Embeddings API error: {response.status_code} - {raw}")

    def fill_collection_if_needed(self):
        if not self._collection_has_data():
            self._create_collection()
            csv_path = os.path.join(os.path.dirname(__file__), "resources", "qa_df_pairs_db.csv")
            points = []
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for idx, row in enumerate(reader):
                    embedding = self._embed(row["question_clear"])
                    points.append(PointStruct(
                        id=idx,
                        vector=embedding,
                        payload={
                            "question_clear": row["question_clear"],
                            "content_clear": row["content_clear"],
                        }
                    ))
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

    def retrieve(self, query: str) -> list[dict]:
        query_embedding = self._embed(query)
        result = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            limit=self.top_n,
            query=query_embedding,
            with_payload=True,
        )
        return result.points


# Singleton instance, created at module level
retrieval_manager = RetrievalManager()
