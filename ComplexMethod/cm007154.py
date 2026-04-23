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
        mapping: dict | None = None,
        max_chunk_bytes: int | None = 1 * 1024 * 1024,
        *,
        is_aoss: bool = False,
    ) -> list[str]:
        """Efficiently ingest multiple documents with embeddings into OpenSearch.

        This method uses bulk operations to insert documents with their vector
        embeddings and metadata into the specified OpenSearch index.

        Args:
            client: OpenSearch client instance
            index_name: Target index for document storage
            embeddings: List of vector embeddings for each document
            texts: List of document texts
            metadatas: Optional metadata dictionaries for each document
            ids: Optional document IDs (UUIDs generated if not provided)
            vector_field: Field name for storing vector embeddings
            text_field: Field name for storing document text
            mapping: Optional index mapping configuration
            max_chunk_bytes: Maximum size per bulk request chunk
            is_aoss: Whether using Amazon OpenSearch Serverless

        Returns:
            List of document IDs that were successfully ingested
        """
        if not mapping:
            mapping = {}

        requests = []
        return_ids = []

        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas else {}
            _id = ids[i] if ids else str(uuid.uuid4())
            request = {
                "_op_type": "index",
                "_index": index_name,
                vector_field: embeddings[i],
                text_field: text,
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
        helpers.bulk(
            client,
            requests,
            max_chunk_bytes=max_chunk_bytes,
            request_timeout=self._get_request_timeout(),
        )
        return return_ids