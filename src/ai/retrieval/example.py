import logging
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_core.stores import BaseStore
from langchain_mongodb.docstores import MongoDBDocStore
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams
from tqdm import tqdm

from settings import settings

logger = logging.getLogger(__name__)


class RetrievalManager:
    """Manager for vector databases and document retrieval."""

    def __init__(self):
        """Initialize retrieval manager with vector stores and document stores."""
        logger.info('🗄️ Инициализация RetrievalManager...')

        self.booklet_vector_store: VectorStore | None = None
        self.booklet_doc_store: BaseStore | None = None
        self.audio_vector_store: VectorStore | None = None
        self.audio_doc_store: BaseStore | None = None
        self.knowledge_vector_store: VectorStore | None = None
        self.knowledge_doc_store: BaseStore | None = None

        # Initialize clients
        self.qdrant_client = QdrantClient(url=settings.ai.retrieval.qdrant.url)
        self.embedding = OpenAIEmbeddings(
            api_key=settings.ai.retrieval.embedder.api_key,
            model=settings.ai.retrieval.embedder.model,
            openai_proxy=settings.ai.retrieval.embedder.proxy_url,
        )
        logger.info('✅ RetrievalManager инициализирован')

    def _init_vector_store(self, collection_name: str) -> tuple[BaseStore, VectorStore]:
        """Initialize vector store and document store for a collection."""
        # Initialize MongoDB document store
        doc_store = MongoDBDocStore.from_connection_string(
            settings.ai.retrieval.mongo.connection_string,
            f'{settings.ai.retrieval.mongo.db_name}.{collection_name}',
        )

        # Create Qdrant collection if it doesn't exist
        try:
            self.qdrant_client.get_collection(collection_name)
        except Exception:
            self.qdrant_client.create_collection(
                collection_name,
                vectors_config=VectorParams(
                    size=settings.ai.retrieval.qdrant.vector_size,
                    distance=settings.ai.retrieval.qdrant.distance_metric,
                ),
            )

        # Initialize vector store
        vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=collection_name,
            embedding=self.embedding,
        )

        return doc_store, vector_store

    def _collection_has_data(self, collection_name: str) -> bool:
        """Check if collection exists and has data."""
        try:
            collection_info = self.qdrant_client.get_collection(collection_name)
            return collection_info.points_count > 0
        except Exception:
            return False

    def _chunk_documents(self, documents: list[Document]) -> list[Document]:
        """Chunk documents using RecursiveCharacterTextSplitter."""
        return RecursiveCharacterTextSplitter(
            chunk_size=settings.ai.retrieval.chunking.chunk_size,
            chunk_overlap=settings.ai.retrieval.chunking.chunk_overlap,
        ).split_documents(documents)

    async def init_booklets_db(self, complexes_dict: dict[str, dict] = None):
        """Initialize booklets vector database with residential complex data."""
        logger.info('🔄 Initializing booklets database...')

        # Always initialize vector store members
        self.booklet_doc_store, self.booklet_vector_store = self._init_vector_store(
            settings.ai.retrieval.qdrant.residential_complex_booklets_collection_name,
        )

        # Check if collection already has data
        if self._collection_has_data(settings.ai.retrieval.qdrant.residential_complex_booklets_collection_name):
            logger.info('✅ Booklets collection already exists and has data, skipping population')
            return

        if complexes_dict is None:
            logger.warning('⚠️ No complexes dictionary provided, skipping booklets initialization')
            return

        booklets_path = settings.data_paths.booklets

        try:
            # Get all booklet files
            booklet_files = [f for f in os.listdir(booklets_path) if f.endswith('.pdf')]
            logger.info(f'Found {len(booklet_files)} booklet files')

            docs: list[Document] = []

            with tqdm(complexes_dict.items(), desc='📖 Loading booklets', unit='complex') as pbar:
                for complex_name, complex_info in pbar:
                    complex_id = complex_info['id']  # Get real database ID
                    pbar.set_postfix_str(f'Processing {complex_name}')

                    file_path = os.path.join(booklets_path, f'{complex_name}.pdf')
                    logger.info(f"Loading booklet for '{complex_name}'")

                    try:
                        loader = PyPDFLoader(
                            file_path,
                            mode='single',
                        )
                        doc: Document = (await loader.aload())[0]

                        # Rewrite metadata
                        doc.metadata = {
                            'source': doc.metadata['source'],
                            'source_type': 'residential_complex_booklet',
                            'related_residential_complex_name': complex_name,
                            'related_residential_complex_id_from_database': complex_id,
                        }

                        # Save the doc
                        docs.append(doc)

                        pbar.set_postfix_str(f'✅ Loaded {complex_name}')
                        logger.info(f"✅ Loaded booklet for '{complex_name}'")

                    except Exception as e:
                        pbar.set_postfix_str(f'❌ Error: {complex_name}')
                        logger.exception(f"❌ Error loading booklet for '{complex_name}': {e}")

            # Store documents in doc store
            await self.booklet_doc_store.amset(
                [(f'{doc.metadata["related_residential_complex_name"]}', doc) for doc in docs]
            )

            # Chunk and add to vector store
            chunks = self._chunk_documents(docs)
            await self.booklet_vector_store.aadd_documents(chunks)

            logger.info(f'✅ Booklets database initialized: {len(docs)}/{len(complexes_dict)} complexes loaded')

        except Exception as e:
            logger.exception(f'❌ Error initializing booklets database: {e}')

    async def init_audio_db(self, complexes_dict: dict[str, dict] = None):  # noqa: C901
        """Initialize audio transcripts vector database with residential complex data."""
        logger.info('🔄 Initializing audio database...')

        # Always initialize vector store members
        self.audio_doc_store, self.audio_vector_store = self._init_vector_store(
            settings.ai.retrieval.qdrant.residential_complex_video_transcripts_collection_name,
        )

        # Check if collection already has data
        if self._collection_has_data(
            settings.ai.retrieval.qdrant.residential_complex_video_transcripts_collection_name
        ):
            logger.info('✅ Audio transcripts collection already exists and has data, skipping population')
            return

        if complexes_dict is None:
            logger.warning('⚠️ No complexes dictionary provided, skipping audio initialization')
            return

        transcripts_path = settings.data_paths.transcripts

        try:
            # Get all transcript files
            transcript_files = [f for f in os.listdir(transcripts_path) if f.endswith('.txt')]
            logger.info(f'Found {len(transcript_files)} transcript files')

            # Filter out general knowledge files
            general_knowledge_patterns = settings.ai.retrieval.general_knowledge_files
            complex_transcript_files = []

            for filename in transcript_files:
                filename_base = os.path.splitext(filename)[0]
                is_general = any(pattern.lower() in filename_base.lower() for pattern in general_knowledge_patterns)
                if not is_general:
                    complex_transcript_files.append(filename)

            logger.info(f'Found {len(complex_transcript_files)} complex-specific transcript files')

            docs_added = 0
            with tqdm(
                complexes_dict.items(),
                desc='🎧 Loading audio transcripts',
                unit='complex',
            ) as pbar:
                for complex_name, complex_info in pbar:
                    complex_id = complex_info['id']  # Get real database ID
                    metadata = complex_info['metadata']  # Get metadata object
                    pbar.set_postfix_str(f'Processing {complex_name}')

                    if not metadata:
                        pbar.set_postfix_str(f'⚠️ No metadata: {complex_name}')
                        logger.warning(f"⚠️ No metadata found for '{complex_name}'")
                        continue

                    # Get transcript filenames from metadata
                    transcript_files_to_process = []

                    if metadata.audio and metadata.audio in complex_transcript_files:
                        transcript_files_to_process.append(('audio', metadata.audio))

                    if metadata.additional_audio and metadata.additional_audio in complex_transcript_files:
                        transcript_files_to_process.append(('additional_audio', metadata.additional_audio))

                    if not transcript_files_to_process:
                        pbar.set_postfix_str(f'⚠️ No transcripts: {complex_name}')
                        logger.warning(f"⚠️ No matching transcript files found for '{complex_name}'")
                        continue

                    # Process each transcript file
                    complex_docs_loaded = 0
                    for audio_type, transcript_file in transcript_files_to_process:
                        file_path = os.path.join(transcripts_path, transcript_file)
                        logger.info(f"Loading {audio_type} transcript for '{complex_name}': {transcript_file}")

                        try:
                            # Load text document
                            loader = TextLoader(file_path, encoding='utf-8')
                            docs = await loader.aload()

                            if docs:
                                # Add metadata
                                for doc in docs:
                                    doc.metadata = {
                                        'source': doc.metadata['source'],
                                        'source_type': 'transcript_of_residential_complex_video',
                                        'related_residential_complex_name': complex_name,
                                        'related_residential_complex_id_from_database': complex_id,
                                    }

                                # Store full documents in doc store
                                await self.audio_doc_store.amset(
                                    [(f'{complex_name}_{audio_type}_{i}', doc) for i, doc in enumerate(docs)]
                                )

                                # Chunk and add to vector store
                                chunks = self._chunk_documents(docs)
                                await self.audio_vector_store.aadd_documents(chunks)

                                complex_docs_loaded += len(docs)
                                logger.info(
                                    f"✅ Loaded {audio_type} transcript for '{complex_name}' ({len(chunks)} chunks)"
                                )

                        except Exception as e:
                            logger.exception(f"❌ Error loading {audio_type} transcript for '{complex_name}': {e}")

                    if complex_docs_loaded > 0:
                        docs_added += 1
                        pbar.set_postfix_str(f'✅ Loaded {complex_name} ({complex_docs_loaded} docs)')
                    else:
                        pbar.set_postfix_str(f'❌ Failed: {complex_name}')

            logger.info(f'✅ Audio database initialized: {docs_added}/{len(complexes_dict)} complexes loaded')

        except Exception as e:
            logger.exception(f'❌ Error initializing audio database: {e}')

    async def init_knowledge_base_db(self):
        """Initialize knowledge base vector database with general real estate knowledge."""
        logger.info('🔄 Initializing knowledge base database...')

        # Always initialize vector store members
        self.knowledge_doc_store, self.knowledge_vector_store = self._init_vector_store(
            settings.ai.retrieval.qdrant.real_estate_knowledge_collection_name,
        )

        # Check if collection already has data
        if self._collection_has_data(settings.ai.retrieval.qdrant.real_estate_knowledge_collection_name):
            logger.info('✅ Knowledge base collection already exists and has data, skipping population')
            return

        transcripts_path = settings.data_paths.transcripts

        try:
            # Get all transcript files
            transcript_files = [f for f in os.listdir(transcripts_path) if f.endswith('.txt')]

            # Filter for general knowledge files
            general_knowledge_patterns = settings.ai.retrieval.general_knowledge_files
            knowledge_files = []

            for filename in transcript_files:
                filename_base = os.path.splitext(filename)[0]
                for pattern in general_knowledge_patterns:
                    if pattern.lower() in filename_base.lower():
                        knowledge_files.append(filename)
                        break

            logger.info(f'Found {len(knowledge_files)} general knowledge files')

            loaded_count = 0
            with tqdm(knowledge_files, desc='🧠 Loading knowledge base', unit='file') as pbar:
                for filename in pbar:
                    pbar.set_postfix_str(f'Processing {filename[:30]}...')

                    file_path = os.path.join(transcripts_path, filename)
                    logger.info(f'Loading knowledge file: {filename}')

                    try:
                        # Load text document
                        loader = TextLoader(file_path, encoding='utf-8')
                        docs = await loader.aload()

                        if docs:
                            # Add metadata
                            for doc in docs:
                                doc.metadata = {
                                    'source': doc.metadata['source'],
                                    'source_type': 'transcript_of_real_estate_video',
                                }

                            # Store full documents in doc store
                            await self.knowledge_doc_store.amset(
                                [(f'knowledge_{loaded_count}_{i}', doc) for i, doc in enumerate(docs)]
                            )

                            # Chunk and add to vector store
                            chunks = self._chunk_documents(docs)
                            await self.knowledge_vector_store.aadd_documents(chunks)

                            loaded_count += 1
                            pbar.set_postfix_str(f'✅ Loaded ({len(chunks)} chunks)')
                            logger.info(f"✅ Loaded knowledge file '{filename}' ({len(chunks)} chunks)")

                    except Exception as e:
                        pbar.set_postfix_str(f'❌ Error: {filename[:20]}...')
                        logger.exception(f"❌ Error loading knowledge file '{filename}': {e}")

            logger.info(f'✅ Knowledge base database initialized: {loaded_count} files loaded')

        except Exception as e:
            logger.exception(f'❌ Error initializing knowledge base database: {e}')