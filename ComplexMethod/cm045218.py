async def add(
        self,
        content: MemoryContent,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> None:
        """Add content to memory.

        Args:
            content: The memory content to add.
            cancellation_token: Optional token to cancel operation.

        Raises:
            Exception: If there's an error adding content to mem0 memory.
        """
        # Extract content based on mime type
        if hasattr(content, "content") and hasattr(content, "mime_type"):
            if content.mime_type in ["text/plain", "text/markdown"]:
                message = str(content.content)
            elif content.mime_type == "application/json":
                # Convert JSON content to string representation
                if isinstance(content.content, str):
                    message = content.content
                else:
                    # Convert dict or other JSON serializable objects to string
                    import json

                    message = json.dumps(content.content)
            else:
                message = str(content.content)

            # Extract metadata
            metadata = content.metadata or {}
        else:
            # Handle case where content is directly provided as string
            message = str(content)
            metadata = {}

        # Check if operation is cancelled
        if cancellation_token is not None and cancellation_token.cancelled:  # type: ignore
            return

        # Add to mem0 client
        try:
            user_id = metadata.pop("user_id", self._user_id)
            # Suppress warning messages from mem0 MemoryClient
            kwargs = {} if self._client.__class__.__name__ == "Memory" else {"output_format": "v1.1"}
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self._client.add([{"role": "user", "content": message}], user_id=user_id, metadata=metadata, **kwargs)  # type: ignore
        except Exception as e:
            # Log the error but don't crash
            logger.error(f"Error adding to mem0 memory: {str(e)}")
            raise