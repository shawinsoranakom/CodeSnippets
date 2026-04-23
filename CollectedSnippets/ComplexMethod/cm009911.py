def _get_builtin_translator(vectorstore: VectorStore) -> Visitor:
    """Get the translator class corresponding to the vector store class."""
    try:
        import langchain_community  # noqa: F401
    except ImportError as err:
        msg = (
            "The langchain-community package must be installed to use this feature."
            " Please install it using `pip install langchain-community`."
        )
        raise ImportError(msg) from err

    from langchain_community.query_constructors.astradb import AstraDBTranslator
    from langchain_community.query_constructors.chroma import ChromaTranslator
    from langchain_community.query_constructors.dashvector import DashvectorTranslator
    from langchain_community.query_constructors.databricks_vector_search import (
        DatabricksVectorSearchTranslator,
    )
    from langchain_community.query_constructors.deeplake import DeepLakeTranslator
    from langchain_community.query_constructors.dingo import DingoDBTranslator
    from langchain_community.query_constructors.elasticsearch import (
        ElasticsearchTranslator,
    )
    from langchain_community.query_constructors.milvus import MilvusTranslator
    from langchain_community.query_constructors.mongodb_atlas import (
        MongoDBAtlasTranslator,
    )
    from langchain_community.query_constructors.myscale import MyScaleTranslator
    from langchain_community.query_constructors.neo4j import Neo4jTranslator
    from langchain_community.query_constructors.opensearch import OpenSearchTranslator
    from langchain_community.query_constructors.pgvector import PGVectorTranslator
    from langchain_community.query_constructors.pinecone import PineconeTranslator
    from langchain_community.query_constructors.qdrant import QdrantTranslator
    from langchain_community.query_constructors.redis import RedisTranslator
    from langchain_community.query_constructors.supabase import SupabaseVectorTranslator
    from langchain_community.query_constructors.tencentvectordb import (
        TencentVectorDBTranslator,
    )
    from langchain_community.query_constructors.timescalevector import (
        TimescaleVectorTranslator,
    )
    from langchain_community.query_constructors.vectara import VectaraTranslator
    from langchain_community.query_constructors.weaviate import WeaviateTranslator
    from langchain_community.vectorstores import (
        AstraDB,
        DashVector,
        DatabricksVectorSearch,
        DeepLake,
        Dingo,
        Milvus,
        MyScale,
        Neo4jVector,
        OpenSearchVectorSearch,
        PGVector,
        Qdrant,
        Redis,
        SupabaseVectorStore,
        TencentVectorDB,
        TimescaleVector,
        Vectara,
        Weaviate,
    )
    from langchain_community.vectorstores import (
        Chroma as CommunityChroma,
    )
    from langchain_community.vectorstores import (
        ElasticsearchStore as ElasticsearchStoreCommunity,
    )
    from langchain_community.vectorstores import (
        MongoDBAtlasVectorSearch as CommunityMongoDBAtlasVectorSearch,
    )
    from langchain_community.vectorstores import (
        Pinecone as CommunityPinecone,
    )

    builtin_translators: dict[type[VectorStore], type[Visitor]] = {
        AstraDB: AstraDBTranslator,
        PGVector: PGVectorTranslator,
        CommunityPinecone: PineconeTranslator,
        CommunityChroma: ChromaTranslator,
        DashVector: DashvectorTranslator,
        Dingo: DingoDBTranslator,
        Weaviate: WeaviateTranslator,
        Vectara: VectaraTranslator,
        Qdrant: QdrantTranslator,
        MyScale: MyScaleTranslator,
        DeepLake: DeepLakeTranslator,
        ElasticsearchStoreCommunity: ElasticsearchTranslator,
        Milvus: MilvusTranslator,
        SupabaseVectorStore: SupabaseVectorTranslator,
        TimescaleVector: TimescaleVectorTranslator,
        OpenSearchVectorSearch: OpenSearchTranslator,
        CommunityMongoDBAtlasVectorSearch: MongoDBAtlasTranslator,
        Neo4jVector: Neo4jTranslator,
    }
    if isinstance(vectorstore, DatabricksVectorSearch):
        return DatabricksVectorSearchTranslator()
    if isinstance(vectorstore, MyScale):
        return MyScaleTranslator(metadata_key=vectorstore.metadata_column)
    if isinstance(vectorstore, Redis):
        return RedisTranslator.from_vectorstore(vectorstore)
    if isinstance(vectorstore, TencentVectorDB):
        fields = [
            field.name for field in (vectorstore.meta_fields or []) if field.index
        ]
        return TencentVectorDBTranslator(fields)
    if vectorstore.__class__ in builtin_translators:
        return builtin_translators[vectorstore.__class__]()
    try:
        from langchain_astradb.vectorstores import AstraDBVectorStore
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, AstraDBVectorStore):
            return AstraDBTranslator()

    try:
        from langchain_elasticsearch.vectorstores import ElasticsearchStore
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, ElasticsearchStore):
            return ElasticsearchTranslator()

    try:
        from langchain_pinecone import PineconeVectorStore
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, PineconeVectorStore):
            return PineconeTranslator()

    try:
        from langchain_milvus import Milvus
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, Milvus):
            return MilvusTranslator()

    try:
        from langchain_mongodb import MongoDBAtlasVectorSearch
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, MongoDBAtlasVectorSearch):
            return MongoDBAtlasTranslator()

    try:
        from langchain_neo4j import Neo4jVector
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, Neo4jVector):
            return Neo4jTranslator()

    try:
        # Trying langchain_chroma import if exists
        from langchain_chroma import Chroma
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, Chroma):
            return ChromaTranslator()

    try:
        from langchain_postgres import PGVector
        from langchain_postgres import PGVectorTranslator as NewPGVectorTranslator
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, PGVector):
            return NewPGVectorTranslator()

    try:
        from langchain_qdrant import QdrantVectorStore
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, QdrantVectorStore):
            return QdrantTranslator(metadata_key=vectorstore.metadata_payload_key)

    try:
        # Added in langchain-community==0.2.11
        from langchain_community.query_constructors.hanavector import HanaTranslator
        from langchain_community.vectorstores import HanaDB
    except ImportError:
        pass
    else:
        if isinstance(vectorstore, HanaDB):
            return HanaTranslator()

    try:
        # Trying langchain_weaviate (weaviate v4) import if exists
        from langchain_weaviate.vectorstores import WeaviateVectorStore

    except ImportError:
        pass
    else:
        if isinstance(vectorstore, WeaviateVectorStore):
            return WeaviateTranslator()

    msg = (
        f"Self query retriever with Vector Store type {vectorstore.__class__}"
        f" not supported."
    )
    raise ValueError(msg)