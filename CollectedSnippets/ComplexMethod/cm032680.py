async def run_graphrag(
    row: dict,
    language,
    with_resolution: bool,
    with_community: bool,
    chat_model,
    embedding_model,
    callback,
):
    enable_timeout_assertion = os.environ.get("ENABLE_TIMEOUT_ASSERTION")
    start = asyncio.get_running_loop().time()
    tenant_id, kb_id, doc_id = row["tenant_id"], str(row["kb_id"]), row["doc_id"]
    chunks = []
    for d in settings.retriever.chunk_list(doc_id, tenant_id, [kb_id], max_count=10000, fields=["content_with_weight", "doc_id"], sort_by_position=True):
        chunks.append(d["content_with_weight"])

    timeout_sec = max(120, len(chunks) * 60 * 10) if enable_timeout_assertion else 10000000000

    try:
        subgraph = await asyncio.wait_for(
            generate_subgraph(
                LightKGExt if "method" not in row["kb_parser_config"].get("graphrag", {})
                    or row["kb_parser_config"]["graphrag"]["method"] != "general"
                else GeneralKGExt,
                tenant_id,
                kb_id,
                doc_id,
                chunks,
                language,
                row["kb_parser_config"]["graphrag"].get("entity_types", []),
                chat_model,
                embedding_model,
                callback,
            ),
            timeout=timeout_sec,
        )
    except asyncio.TimeoutError:
        logging.error("generate_subgraph timeout")
        raise

    if not subgraph:
        return

    graphrag_task_lock = RedisDistributedLock(f"graphrag_task_{kb_id}", lock_value=doc_id, timeout=1200)
    await graphrag_task_lock.spin_acquire()
    callback(msg=f"run_graphrag {doc_id} graphrag_task_lock acquired")

    try:
        subgraph_nodes = set(subgraph.nodes())
        new_graph = await merge_subgraph(
            tenant_id,
            kb_id,
            doc_id,
            subgraph,
            embedding_model,
            callback,
        )
        assert new_graph is not None

        if not with_resolution and not with_community:
            return

        if with_resolution:
            await graphrag_task_lock.spin_acquire()
            callback(msg=f"run_graphrag {doc_id} graphrag_task_lock acquired")
            await resolve_entities(
                new_graph,
                subgraph_nodes,
                tenant_id,
                kb_id,
                doc_id,
                chat_model,
                embedding_model,
                callback,
                task_id=row["id"],
            )
        if with_community:
            await graphrag_task_lock.spin_acquire()
            callback(msg=f"run_graphrag {doc_id} graphrag_task_lock acquired")
            await extract_community(
                new_graph,
                tenant_id,
                kb_id,
                doc_id,
                chat_model,
                embedding_model,
                callback,
                task_id=row["id"],
            )
    finally:
        graphrag_task_lock.release()
    now = asyncio.get_running_loop().time()
    callback(msg=f"GraphRAG for doc {doc_id} done in {now - start:.2f} seconds.")
    return