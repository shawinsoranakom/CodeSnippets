def _bulk_ingest_embeddings(
        self,
        client: OpenSearch,
        index_name: str,
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
        vector_field: str = "vector_field",
        text_field: str = "text",
        embedding_model: str = "unknown",
        mapping: dict | None = None,
        max_chunk_bytes: int | None = 1 * 1024 * 1024,
        *,
        is_aoss: bool = False,
    ) -> list[str]:
        """Efficiently ingest multiple documents with embeddings into OpenSearch.

        This method uses bulk operations to insert documents with their vector
        embeddings and metadata into the specified OpenSearch index. Each document
        is tagged with the embedding_model name for tracking.

        Args:
            client: OpenSearch client instance
            index_name: Target index for document storage
            embeddings: List of vector embeddings for each document
            texts: List of document texts
            metadatas: Optional metadata dictionaries for each document
            ids: Optional document IDs (UUIDs generated if not provided)
            vector_field: Field name for storing vector embeddings
            text_field: Field name for storing document text
            embedding_model: Name of the embedding model used
            mapping: Optional index mapping configuration
            max_chunk_bytes: Maximum size per bulk request chunk
            is_aoss: Whether using Amazon OpenSearch Serverless

        Returns:
            List of document IDs that were successfully ingested
        """
        logger.debug(f"[OpenSearchMultimodel] Bulk ingesting embeddings for {index_name}")
        if not mapping:
            mapping = {}

        requests = []
        return_ids = []
        vector_dimensions = len(embeddings[0]) if embeddings else None

        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas else {}
            if vector_dimensions is not None and "embedding_dimensions" not in metadata:
                metadata = {**metadata, "embedding_dimensions": vector_dimensions}

            # Normalize ACL fields that may arrive as JSON strings from flows
            for key in ("allowed_users", "allowed_groups"):
                value = metadata.get(key)
                if isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, list):
                            metadata[key] = parsed
                    except (json.JSONDecodeError, TypeError):
                        # Leave value as-is if it isn't valid JSON
                        pass

            _id = ids[i] if ids else str(uuid.uuid4())
            request = {
                "_op_type": "index",
                "_index": index_name,
                vector_field: embeddings[i],
                text_field: text,
                "embedding_model": embedding_model,  # Track which model was used
                **metadata,
            }
            if is_aoss:
                request["id"] = _id
            else:
                request["_id"] = _id
            requests.append(request)
            return_ids.append(_id)
        if metadatas:
            self.log(f"Sample metadata: {metadatas[0] if metadatas else {}}")
        helpers.bulk(client, requests, max_chunk_bytes=max_chunk_bytes)
        return return_ids