async def query(
        self,
        query: str | MemoryContent = "",
        cancellation_token: Optional[CancellationToken] = None,
        **kwargs: Any,
    ) -> MemoryQueryResult:
        """Query memory for relevant content.

        Args:
            query: The query to search for, either as string or MemoryContent.
            cancellation_token: Optional token to cancel operation.
            **kwargs: Additional query parameters to pass to mem0.

        Returns:
            MemoryQueryResult containing search results.
        """
        # Extract query text
        if isinstance(query, str):
            query_text = query
        elif hasattr(query, "content"):
            query_text = str(query.content)
        else:
            query_text = str(query)

        # Check if operation is cancelled
        if (
            cancellation_token
            and hasattr(cancellation_token, "cancelled")
            and getattr(cancellation_token, "cancelled", False)
        ):
            return MemoryQueryResult(results=[])

        try:
            limit = kwargs.pop("limit", self._limit)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                # Query mem0 client
                results = self._client.search(  # type: ignore
                    query_text,
                    user_id=self._user_id,
                    limit=limit,
                    **kwargs,
                )

                # Type-safe handling of results
                if isinstance(results, dict) and "results" in results:
                    result_list = cast(List[MemoryResult], results["results"])
                else:
                    result_list = cast(List[MemoryResult], results)

            # Convert results to MemoryContent objects
            memory_contents: List[MemoryContent] = []
            for result in result_list:
                content_text = result.get("memory", "")
                metadata: Dict[str, Any] = {}

                if "metadata" in result and result["metadata"]:
                    metadata = result["metadata"]

                # Add relevant fields to metadata
                if "score" in result:
                    metadata["score"] = result["score"]

                # For created_at
                if "created_at" in result and result.get("created_at"):
                    try:
                        metadata["created_at"] = datetime.fromisoformat(result["created_at"])
                    except (ValueError, TypeError):
                        pass

                # For updated_at
                if "updated_at" in result and result.get("updated_at"):
                    try:
                        metadata["updated_at"] = datetime.fromisoformat(result["updated_at"])
                    except (ValueError, TypeError):
                        pass

                # For categories
                if "categories" in result and result.get("categories"):
                    metadata["categories"] = result["categories"]

                # Create MemoryContent object
                memory_content = MemoryContent(
                    content=content_text,
                    mime_type="text/plain",  # Default to text/plain
                    metadata=metadata,
                )
                memory_contents.append(memory_content)

            return MemoryQueryResult(results=memory_contents)

        except Exception as e:
            # Log the error but return empty results
            logger.error(f"Error querying mem0 memory: {str(e)}")
            return MemoryQueryResult(results=[])