async def get_knowledge_base_chunks(
    kb_name: str,
    current_user: CurrentActiveUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    search: Annotated[str, Query(description="Filter chunks whose text contains this substring")] = "",
) -> PaginatedChunkResponse:
    """Get chunks from a specific knowledge base with pagination."""
    kb_path: Path | None = None
    try:
        kb_path = _resolve_kb_path(kb_name, current_user)

        # Guard: If no physical chroma data exists, return empty response immediately
        # This prevents 'readonly database' errors when trying to initialize Chroma on an empty directory
        has_data = any((kb_path / m).exists() for m in ["chroma", "chroma.sqlite3", "index"])
        if not has_data:
            return PaginatedChunkResponse(
                chunks=[],
                total=0,
                page=page,
                limit=limit,
                total_pages=0,
            )

        # Create vector store
        client = KBStorageHelper.get_fresh_chroma_client(kb_path)
        chroma = Chroma(
            client=client,
            collection_name=kb_name,
        )

        # Access the raw collection
        collection = chroma._collection  # noqa: SLF001

        search_term = search.strip()

        if search_term:
            # When searching, fetch all matching docs then paginate in-memory
            where_doc = {"$contains": search_term}
            all_results = collection.get(
                include=["documents", "metadatas"],
                where_document=where_doc,
            )
            total_count = len(all_results["ids"])
            offset = (page - 1) * limit
            sliced_ids = all_results["ids"][offset : offset + limit]
            sliced_docs = all_results["documents"][offset : offset + limit]
            sliced_metas = all_results["metadatas"][offset : offset + limit]
        else:
            # No search - use Chroma's native pagination
            total_count = collection.count()
            offset = (page - 1) * limit
            results = collection.get(
                include=["documents", "metadatas"],
                limit=limit,
                offset=offset,
            )
            sliced_ids = results["ids"]
            sliced_docs = results["documents"]
            sliced_metas = results["metadatas"]

        chunks = []
        for doc_id, document, metadata in zip(sliced_ids, sliced_docs, sliced_metas, strict=False):
            content = document or ""
            chunks.append(
                ChunkInfo(
                    id=doc_id,
                    content=content,
                    char_count=len(content),
                    metadata=metadata,
                )
            )
        return PaginatedChunkResponse(
            chunks=chunks,
            total=total_count,
            page=page,
            limit=limit,
            total_pages=(total_count + limit - 1) // limit if total_count > 0 else 0,
        )

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("Error getting chunks for '%s': %s", kb_name, e)
        raise HTTPException(status_code=500, detail="Error getting chunks.") from e
    finally:
        client = None
        chroma = None
        if kb_path is not None:
            KBStorageHelper.release_chroma_resources(kb_path)