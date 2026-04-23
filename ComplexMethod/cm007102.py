async def retrieve_data(self) -> DataFrame:
        """Retrieve data from the selected knowledge base by reading the Chroma collection.

        Returns:
            A DataFrame containing the data rows from the knowledge base.
        """
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(astra_error_msg)
        # Get the current user
        async with session_scope() as db:
            if not self.user_id:
                msg = "User ID is required for fetching Knowledge Base data."
                raise ValueError(msg)
            current_user = await get_user_by_id(db, self.user_id)
            if not current_user:
                msg = f"User with ID {self.user_id} not found."
                raise ValueError(msg)
            kb_user = current_user.username
        kb_path = _get_knowledge_bases_root_path() / kb_user / self.knowledge_base

        metadata = self._get_kb_metadata(kb_path)
        if not metadata:
            msg = f"Metadata not found for knowledge base: {self.knowledge_base}. Ensure it has been indexed."
            raise ValueError(msg)

        # Resolve API key: user override > metadata (decrypted) > global variable
        provider = metadata.get("embedding_provider")
        runtime_api_key = self.api_key.get_secret_value() if isinstance(self.api_key, SecretStr) else self.api_key
        api_key = runtime_api_key or metadata.get("api_key")
        if not api_key and provider:
            api_key = await self._resolve_api_key(provider)

        # Resolve provider-specific variables (e.g. base_url for Ollama, project_id for WatsonX)
        provider_vars: dict[str, str] = {}
        if provider in {"Ollama", "IBM WatsonX"}:
            provider_vars = await self._resolve_provider_variables(provider)

        # Build the embedder for the knowledge base
        embedding_function = self._build_embeddings(metadata, api_key=api_key, provider_vars=provider_vars)

        # Clear Chroma's singleton client cache to avoid "different settings"
        # conflicts when ingestion and retrieval run in the same process.
        chromadb.api.client.SharedSystemClient.clear_system_cache()
        chroma = Chroma(
            persist_directory=str(kb_path),
            embedding_function=embedding_function,
            collection_name=self.knowledge_base,
        )

        # If a search query is provided, perform a similarity search
        if self.search_query:
            # Use the search query to perform a similarity search
            logger.info("Performing similarity search")
            results = chroma.similarity_search_with_score(
                query=self.search_query or "",
                k=self.top_k,
            )
        else:
            results = chroma.similarity_search(
                query=self.search_query or "",
                k=self.top_k,
            )

            # For each result, make it a tuple to match the expected output format
            results = [(doc, 0) for doc in results]  # Assign a dummy score of 0

        # If include_embeddings is enabled, get embeddings for the results
        id_to_embedding = {}
        if self.include_embeddings and results:
            doc_ids = [doc[0].metadata.get("_id") for doc in results if doc[0].metadata.get("_id")]

            # Only proceed if we have valid document IDs
            if doc_ids:
                # Access underlying collection to get embeddings
                collection = chroma._collection  # noqa: SLF001
                embeddings_result = collection.get(where={"_id": {"$in": doc_ids}}, include=["metadatas", "embeddings"])

                # Create a mapping from document ID to embedding
                for i, metadata in enumerate(embeddings_result.get("metadatas", [])):
                    if metadata and "_id" in metadata:
                        id_to_embedding[metadata["_id"]] = embeddings_result["embeddings"][i]

        # Build output data based on include_metadata setting
        data_list = []
        for doc in results:
            kwargs = {
                "content": doc[0].page_content,
            }
            if self.search_query:
                kwargs["_score"] = -1 * doc[1]
            if self.include_metadata:
                # Include all metadata, embeddings, and content
                kwargs.update(doc[0].metadata)
            if self.include_embeddings:
                kwargs["_embeddings"] = id_to_embedding.get(doc[0].metadata.get("_id"))

            data_list.append(Data(**kwargs))

        # Return the DataFrame containing the data
        return DataFrame(data=data_list)