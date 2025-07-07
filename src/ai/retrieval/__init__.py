# Standard library imports
import csv
import logging
import os

# External library imports
import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams

# Internal module imports
from src.settings import settings


# Configure module-level logging
logger = logging.getLogger(__name__)


class RetrievalManager:
    """Manages vector-based retrieval of question-answer pairs using Qdrant.
    
    This class handles the initialization, population, and querying of a Qdrant
    vector database containing question-answer pairs for knowledge retrieval.
    """

    def __init__(self):
        """Initialize the retrieval manager with Qdrant client and configuration."""
        logger.info("Initializing RetrievalManager")
        
        self.qdrant_client = QdrantClient(url=settings.qdrant.URL)
        self.collection_name = settings.qdrant.QA_COLLECTION_NAME
        self.vector_size = 768  # Standard embedding dimension
        self.distance_metric = "Cosine"  # Cosine similarity for text embeddings
        self.top_results_count = settings.qdrant.TOP_N
        
        logger.info(f"Configured for collection '{self.collection_name}' "
                   f"with vector size {self.vector_size}")
        
        self.ensure_collection_populated()

    def _check_collection_has_data(self) -> bool:
        """Check if the collection exists and contains data.
        
        Returns:
            True if collection exists and has points, False otherwise
        """
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            has_data = collection_info.points_count > 0
            logger.info(f"Collection '{self.collection_name}' has {collection_info.points_count} points")
            return has_data
        except Exception as e:
            logger.warning(f"Collection check failed: {e}")
            return False

    def _create_collection(self):
        """Create a new Qdrant collection with appropriate vector configuration."""
        logger.info(f"Creating new collection '{self.collection_name}'")
        
        self.qdrant_client.create_collection(
            self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=self.distance_metric,
            ),
        )
        
        logger.info("Collection created successfully")

    def _generate_text_embedding(self, text: str) -> list[float]:
        """Generate embedding for the given text using the configured embedder.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the text embedding
            
        Raises:
            Exception: If the embedding API call fails
        """
        embedder_endpoint = f"{settings.embedder.API_BASE_URL}/embeddings"
        headers = {"Content-Type": "application/json"}
        payload = {"model": settings.embedder.MODEL_NAME, "input": [text]}
        
        logger.debug(f"Generating embedding for text: {text[:50]}...")
        
        with httpx.Client() as client:
            print(embedder_endpoint)
            logger.warning(embedder_endpoint)
            response = client.post(embedder_endpoint, headers=headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                embedding = response_data.get("data", [])[0].get("embedding", [])
                logger.debug(f"Generated embedding with {len(embedding)} dimensions")
                return embedding
            else:
                error_msg = f"Embeddings API error: {response.status_code} - {response_data}"
                logger.error(error_msg)
                raise Exception(error_msg)

    def ensure_collection_populated(self):
        """Ensure the collection exists and is populated with data from CSV file."""
        if not self._check_collection_has_data():
            logger.info("Collection needs to be populated with data")
            self._create_collection()
            self._populate_collection_from_csv()
        else:
            logger.info("Collection already contains data")

    def _populate_collection_from_csv(self):
        """Populate the collection with QA pairs from the CSV resource file."""
        csv_file_path = os.path.join(
            os.path.dirname(__file__), "resources", "qa_df_pairs_db.csv"
        )
        
        logger.info(f"Loading QA pairs from {csv_file_path}")
        
        points = []
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            
            for idx, row in enumerate(csv_reader):
                # Generate embedding for the question
                question_embedding = self._generate_text_embedding(row["question_clear"])
                
                # Create point structure for Qdrant
                point = PointStruct(
                    id=idx,
                    vector=question_embedding,
                    payload={
                        "question_clear": row["question_clear"],
                        "content_clear": row["content_clear"],
                    }
                )
                points.append(point)
                
                if (idx + 1) % 100 == 0:
                    logger.info(f"Processed {idx + 1} QA pairs")
        
        logger.info(f"Upserting {len(points)} points to collection")
        
        # Insert all points into the collection
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info("Collection population completed successfully")

    def retrieve_similar_qa_pairs(self, query: str) -> list[dict]:
        """Retrieve similar question-answer pairs for the given query.
        
        Args:
            query: Search query text
            
        Returns:
            List of scored points containing similar QA pairs
        """
        logger.info(f"Retrieving similar QA pairs for query: {query[:50]}...")
        
        # Generate embedding for the query
        query_embedding = self._generate_text_embedding(query)
        
        # Search for similar vectors in the collection
        search_result = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            limit=self.top_results_count,
            query=query_embedding,
            with_payload=True,
        )
        
        logger.info(f"Retrieved {len(search_result.points)} similar QA pairs")
        return search_result.points

    # Backward compatibility alias
    def retrieve(self, query: str) -> list[dict]:
        """Backward compatibility method for retrieving similar QA pairs."""
        return self.retrieve_similar_qa_pairs(query)


# Singleton instance for global access
retrieval_manager = RetrievalManager()
