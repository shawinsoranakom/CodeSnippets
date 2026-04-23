async def run(
        self, input_data: Input, *, execution_context: ExecutionContext, **_kwargs
    ) -> BlockOutput:
        # Store the media file properly (handles URLs, data URIs, etc.)
        stored_file_path = await store_media_file(
            file=input_data.file_input,
            execution_context=execution_context,
            return_format="for_local_processing",
        )

        # Get full file path (graph_exec_id validated by store_media_file above)
        if not execution_context.graph_exec_id:
            raise ValueError("execution_context.graph_exec_id is required")
        file_path = get_exec_file_path(
            execution_context.graph_exec_id, stored_file_path
        )

        if not Path(file_path).exists():
            raise ValueError(f"File does not exist: {file_path}")

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        except UnicodeDecodeError:
            # Try with different encodings
            try:
                with open(file_path, "r", encoding="latin-1") as file:
                    content = file.read()
            except Exception as e:
                raise ValueError(f"Unable to read file: {e}")

        # Apply skip_size (character-level skip)
        if input_data.skip_size > 0:
            content = content[input_data.skip_size :]

        # Split content into items (by delimiter or treat as single item)
        items = (
            content.split(input_data.delimiter) if input_data.delimiter else [content]
        )

        # Apply skip_rows (item-level skip)
        if input_data.skip_rows > 0:
            items = items[input_data.skip_rows :]

        # Apply row_limit (item-level limit)
        if input_data.row_limit > 0:
            items = items[: input_data.row_limit]

        # Process each item and create chunks
        def create_chunks(text, size_limit):
            """Create chunks from text based on size_limit"""
            if size_limit <= 0:
                return [text] if text else []

            chunks = []
            for i in range(0, len(text), size_limit):
                chunk = text[i : i + size_limit]
                if chunk:  # Only add non-empty chunks
                    chunks.append(chunk)
            return chunks

        # Process items and yield as content chunks
        if items:
            full_content = (
                input_data.delimiter.join(items)
                if input_data.delimiter
                else "".join(items)
            )

            # Create chunks of the full content based on size_limit
            content_chunks = create_chunks(full_content, input_data.size_limit)
            for chunk in content_chunks:
                yield "content", chunk
        else:
            yield "content", ""