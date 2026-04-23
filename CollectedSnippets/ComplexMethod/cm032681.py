async def run_graphrag_for_kb(
    row: dict,
    doc_ids: list[str],
    language: str,
    kb_parser_config: dict,
    chat_model,
    embedding_model,
    callback,
    *,
    with_resolution: bool = True,
    with_community: bool = True,
    max_parallel_docs: int = 4,
) -> dict:
    tenant_id, kb_id = row["tenant_id"], row["kb_id"]
    enable_timeout_assertion = os.environ.get("ENABLE_TIMEOUT_ASSERTION")
    start = asyncio.get_running_loop().time()
    fields_for_chunks = ["content_with_weight", "doc_id"]

    if not doc_ids:
        logging.info(f"Fetching all docs for {kb_id}")
        docs, _ = DocumentService.get_by_kb_id(
            kb_id=kb_id,
            page_number=0,
            items_per_page=0,
            orderby="create_time",
            desc=False,
            keywords="",
            run_status=[],
            types=[],
            suffix=[],
        )
        doc_ids = [doc["id"] for doc in docs]

    doc_ids = list(dict.fromkeys(doc_ids))
    if not doc_ids:
        callback(msg=f"[GraphRAG] kb:{kb_id} has no processable doc_id.")
        return {"ok_docs": [], "failed_docs": [], "total_docs": 0, "total_chunks": 0, "seconds": 0.0}

    def load_doc_chunks(doc_id: str) -> list[str]:
        from common.token_utils import num_tokens_from_string

        chunks = []
        current_chunk = ""

        # DEBUG: Obtener todos los chunks primero
        raw_chunks = list(settings.retriever.chunk_list(
            doc_id,
            tenant_id,
            [kb_id],
            max_count=10000,  # FIX: Aumentar límite para procesar todos los chunks
            fields=fields_for_chunks,
            sort_by_position=True,
        ))

        callback(msg=f"[DEBUG] chunk_list() returned {len(raw_chunks)} raw chunks for doc {doc_id}")

        for d in raw_chunks:
            content = d["content_with_weight"]
            if num_tokens_from_string(current_chunk + content) < 4096:
                current_chunk += content
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = content

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    all_doc_chunks: dict[str, list[str]] = {}
    total_chunks = 0
    for doc_id in doc_ids:
        chunks = load_doc_chunks(doc_id)
        all_doc_chunks[doc_id] = chunks
        total_chunks += len(chunks)

    if total_chunks == 0:
        callback(msg=f"[GraphRAG] kb:{kb_id} has no available chunks in all documents, skip.")
        return {"ok_docs": [], "failed_docs": doc_ids, "total_docs": len(doc_ids), "total_chunks": 0, "seconds": 0.0}

    semaphore = asyncio.Semaphore(max_parallel_docs)

    subgraphs: dict[str, object] = {}
    failed_docs: list[tuple[str, str]] = []  # (doc_id, error)

    async def build_one(doc_id: str):
        if has_canceled(row["id"]):
            callback(msg=f"Task {row['id']} cancelled, stopping execution.")
            raise TaskCanceledException(f"Task {row['id']} was cancelled")

        chunks = all_doc_chunks.get(doc_id, [])
        if not chunks:
            callback(msg=f"[GraphRAG] doc:{doc_id} has no available chunks, skip generation.")
            return

        kg_extractor = LightKGExt if ("method" not in kb_parser_config.get("graphrag", {}) or kb_parser_config["graphrag"]["method"] != "general") else GeneralKGExt

        deadline = max(120, len(chunks) * 60 * 10) if enable_timeout_assertion else 10000000000

        async with semaphore:
            # CHECKPOINT: bounded by semaphore so doc-store lookups respect max_parallel_docs
            existing_sg = await load_subgraph_from_store(tenant_id, kb_id, doc_id)
            if existing_sg:
                subgraphs[doc_id] = existing_sg
                callback(msg=f"[GraphRAG] doc:{doc_id} subgraph found in store, skipping LLM extraction.")
                return
            try:
                msg = f"[GraphRAG] build_subgraph doc:{doc_id}"
                callback(msg=f"{msg} start (chunks={len(chunks)}, timeout={deadline}s)")

                try:
                    sg = await asyncio.wait_for(
                        generate_subgraph(
                            kg_extractor,
                            tenant_id,
                            kb_id,
                            doc_id,
                            chunks,
                            language,
                            kb_parser_config.get("graphrag", {}).get("entity_types", []),
                            chat_model,
                            embedding_model,
                            callback,
                            task_id=row["id"]
                        ),
                        timeout=deadline,
                    )
                except asyncio.TimeoutError:
                    failed_docs.append((doc_id, "timeout"))
                    callback(msg=f"{msg} FAILED: timeout")
                    return
                if sg:
                    subgraphs[doc_id] = sg
                    callback(msg=f"{msg} done")
                else:
                    failed_docs.append((doc_id, "subgraph is empty"))
                    callback(msg=f"{msg} empty")
            except TaskCanceledException as canceled:
                callback(msg=f"[GraphRAG] build_subgraph doc:{doc_id} FAILED: {canceled}")
            except Exception as e:
                failed_docs.append((doc_id, repr(e)))
                callback(msg=f"[GraphRAG] build_subgraph doc:{doc_id} FAILED: {e!r}")

    if has_canceled(row["id"]):
        callback(msg=f"Task {row['id']} cancelled before processing documents.")
        raise TaskCanceledException(f"Task {row['id']} was cancelled")

    tasks = [asyncio.create_task(build_one(doc_id)) for doc_id in doc_ids]
    try:
        await asyncio.gather(*tasks, return_exceptions=False)
    except Exception as e:
        logging.error(f"Error in asyncio.gather: {e}")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise

    if has_canceled(row["id"]):
        callback(msg=f"Task {row['id']} cancelled after document processing.")
        raise TaskCanceledException(f"Task {row['id']} was cancelled")

    ok_docs = [d for d in doc_ids if d in subgraphs]
    if not ok_docs:
        callback(msg=f"[GraphRAG] kb:{kb_id} no subgraphs generated successfully, end.")
        now = asyncio.get_running_loop().time()
        return {"ok_docs": [], "failed_docs": failed_docs, "total_docs": len(doc_ids), "total_chunks": total_chunks, "seconds": now - start}

    kb_lock = RedisDistributedLock(f"graphrag_task_{kb_id}", lock_value="batch_merge", timeout=1200)
    await kb_lock.spin_acquire()
    callback(msg=f"[GraphRAG] kb:{kb_id} merge lock acquired")

    if has_canceled(row["id"]):
        callback(msg=f"Task {row['id']} cancelled before merging subgraphs.")
        raise TaskCanceledException(f"Task {row['id']} was cancelled")

    try:
        union_nodes: set = set()
        final_graph = None

        for doc_id in ok_docs:
            sg = subgraphs[doc_id]
            union_nodes.update(set(sg.nodes()))

            new_graph = await merge_subgraph(
                tenant_id,
                kb_id,
                doc_id,
                sg,
                embedding_model,
                callback,
            )
            if new_graph is not None:
                final_graph = new_graph

        if final_graph is None:
            callback(msg=f"[GraphRAG] kb:{kb_id} merge finished (no in-memory graph returned).")
        else:
            callback(msg=f"[GraphRAG] kb:{kb_id} merge finished, graph ready.")
    finally:
        kb_lock.release()

    if not with_resolution and not with_community:
        now = asyncio.get_running_loop().time()
        callback(msg=f"[GraphRAG] KB merge done in {now - start:.2f}s. ok={len(ok_docs)} / total={len(doc_ids)}")
        return {"ok_docs": ok_docs, "failed_docs": failed_docs, "total_docs": len(doc_ids), "total_chunks": total_chunks, "seconds": now - start}

    if has_canceled(row["id"]):
        callback(msg=f"Task {row['id']} cancelled before resolution/community extraction.")
        raise TaskCanceledException(f"Task {row['id']} was cancelled")

    await kb_lock.spin_acquire()
    callback(msg=f"[GraphRAG] kb:{kb_id} post-merge lock acquired for resolution/community")

    try:
        subgraph_nodes = set()
        for sg in subgraphs.values():
            subgraph_nodes.update(set(sg.nodes()))

        if with_resolution:
            await resolve_entities(
                final_graph,
                subgraph_nodes,
                tenant_id,
                kb_id,
                None,
                chat_model,
                embedding_model,
                callback,
                task_id=row["id"],
            )

        if with_community:
            await extract_community(
                final_graph,
                tenant_id,
                kb_id,
                None,
                chat_model,
                embedding_model,
                callback,
                task_id=row["id"],
            )
    finally:
        kb_lock.release()

    now = asyncio.get_running_loop().time()
    callback(msg=f"[GraphRAG] GraphRAG for KB {kb_id} done in {now - start:.2f} seconds. ok={len(ok_docs)} failed={len(failed_docs)} total_docs={len(doc_ids)} total_chunks={total_chunks}")
    return {
        "ok_docs": ok_docs,
        "failed_docs": failed_docs,  # [(doc_id, error), ...]
        "total_docs": len(doc_ids),
        "total_chunks": total_chunks,
        "seconds": now - start,
    }