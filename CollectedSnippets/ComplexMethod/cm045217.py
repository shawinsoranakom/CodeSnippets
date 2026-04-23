async def query(
        self,
        query: str | MemoryContent,
        cancellation_token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> MemoryQueryResult:
        """Query memory content based on semantic vector similarity.

        .. note::

            RedisMemory.query() supports additional keyword arguments to improve query performance.
            top_k (int): The maximum number of relevant memories to include. Defaults to 10.
            distance_threshold (float): The maximum distance in vector space to consider a memory
            semantically similar when performining cosine similarity search. Defaults to 0.7.
            sequential (bool): Ignore semantic similarity and return the top_k most recent memories.

        Args:
            query (str | MemoryContent): query to perform vector similarity search with. If a
                string is passed, a vector embedding is created from it with the model specified
                in the RedisMemoryConfig. If a MemoryContent object is passed, the content field
                of this object is extracted and a vector embedding is created from it with the
                model specified in the RedisMemoryConfig.
            cancellation_token (CancellationToken): Token passed to cease operation. Not used.

        Returns:
            memoryQueryResult: Object containing memories relevant to the provided query.
        """
        top_k = kwargs.pop("top_k", self.config.top_k)
        distance_threshold = kwargs.pop("distance_threshold", self.config.distance_threshold)

        # return empty results for empty/whitespace queries
        if isinstance(query, str) and not query.strip():
            return MemoryQueryResult(results=[])

        # if sequential memory is requested skip prompt creation
        sequential = bool(kwargs.pop("sequential", self.config.sequential))
        if self.config.sequential and not sequential:
            raise ValueError(
                "Non-sequential queries cannot be run with an underlying sequential RedisMemory. Set sequential=False in RedisMemoryConfig to enable semantic memory querying."
            )
        elif sequential or self.config.sequential:
            results = self.message_history.get_recent(
                top_k=top_k,
                raw=False,
            )
        else:
            # get the query string, or raise an error for unsupported MemoryContent types
            if isinstance(query, str):
                prompt = query
            elif isinstance(query, MemoryContent):
                if query.mime_type in (MemoryMimeType.TEXT, MemoryMimeType.MARKDOWN):
                    prompt = str(query.content)
                elif query.mime_type == MemoryMimeType.JSON:
                    prompt = serialize(query.content)
                else:
                    raise NotImplementedError(
                        f"Error: {query.mime_type} is not supported. Only MemoryMimeType.TEXT, MemoryMimeType.JSON, MemoryMimeType.MARKDOWN are currently supported."
                    )
            else:
                raise TypeError("'query' must be either a string or MemoryContent")

            results = self.message_history.get_relevant(  # type: ignore
                prompt=prompt,  # type: ignore[reportArgumentType]
                top_k=top_k,
                distance_threshold=distance_threshold,
                raw=False,
            )

        memories: List[MemoryContent] = []
        for result in results:  # type: ignore[reportUnkownVariableType]
            metadata = deserialize(result["metadata"])  # type: ignore[reportArgumentType]
            mime_type = MemoryMimeType(metadata.pop("mime_type"))
            if mime_type in (MemoryMimeType.TEXT, MemoryMimeType.MARKDOWN):
                memory_content = result["content"]  # type: ignore[reportArgumentType]
            elif mime_type == MemoryMimeType.JSON:
                memory_content = deserialize(result["content"])  # type: ignore[reportArgumentType]
            else:
                raise NotImplementedError(
                    f"Error: {mime_type} is not supported. Only MemoryMimeType.TEXT, MemoryMimeType.JSON, and MemoryMimeType.MARKDOWN are currently supported."
                )
            memory = MemoryContent(
                content=memory_content,  # type: ignore[reportArgumentType]
                mime_type=mime_type,
                metadata=metadata,
            )
            memories.append(memory)  # type: ignore[reportUknownMemberType]

        return MemoryQueryResult(results=memories)