async def preview_chunks(
    _current_user: CurrentActiveUser,
    files: Annotated[list[UploadFile], File(description="Files to preview chunking for")],
    chunk_size: Annotated[int, Form()] = 1000,
    chunk_overlap: Annotated[int, Form()] = 200,
    separator: Annotated[str, Form()] = "\n",
    max_chunks: Annotated[int, Form()] = 5,
) -> dict[str, object]:
    """Preview how files will be chunked without storing anything.

    Uses the same RecursiveCharacterTextSplitter as the ingest endpoint
    so the preview accurately reflects what will be stored.
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        # Build separators list: user separator first, then defaults
        separators = None
        if separator:
            # Unescape common escape sequences
            actual_separator = separator.replace("\\n", "\n").replace("\\t", "\t")
            separators = [actual_separator, "\n\n", "\n", " ", ""]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
        )

        file_previews: list[dict[str, Any]] = []
        for uploaded_file in files:
            try:
                file_content = await uploaded_file.read()
                file_name = uploaded_file.filename or "unknown"
                text_content = extract_text_from_bytes(file_name, file_content)

                if not text_content.strip():
                    file_previews.append(
                        {
                            "file_name": file_name,
                            "total_chunks": 0,
                            "preview_chunks": [],
                        }
                    )
                    continue

                # Only process enough text for the requested preview chunks
                # to avoid splitting the entire file (which is slow for large files)
                preview_text_limit = max_chunks * chunk_size * CHUNK_PREVIEW_MULTIPLIER
                preview_text = text_content[:preview_text_limit]
                chunks = text_splitter.split_text(preview_text)

                # Estimate total chunks from full text length
                effective_step = max(chunk_size - chunk_overlap, 1)
                estimated_total = max(
                    len(chunks),
                    int((len(text_content) - chunk_overlap) / effective_step),
                )

                # Track character positions for metadata
                preview_chunks = []
                position = 0
                for i, chunk in enumerate(chunks[:max_chunks]):
                    # Find the actual position of this chunk in the original text
                    chunk_start = text_content.find(chunk, position)
                    if chunk_start == -1:
                        chunk_start = position
                    chunk_end = chunk_start + len(chunk)

                    preview_chunks.append(
                        {
                            "content": chunk,
                            "index": i,
                            "char_count": len(chunk),
                            "start": chunk_start,
                            "end": chunk_end,
                        }
                    )
                    position = chunk_start + 1

                file_previews.append(
                    {
                        "file_name": file_name,
                        "total_chunks": estimated_total,
                        "preview_chunks": preview_chunks,
                    }
                )

            except (OSError, ValueError, TypeError) as file_error:
                logger.warning("Error previewing file %s: %s", uploaded_file.filename, file_error)
                file_previews.append(
                    {
                        "file_name": uploaded_file.filename or "unknown",
                        "total_chunks": 0,
                        "preview_chunks": [],
                    }
                )

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("Error previewing chunks: %s", e)
        raise HTTPException(status_code=500, detail="Error previewing chunks.") from e
    else:
        return {"files": file_previews}