async def set_graph(tenant_id: str, kb_id: str, embd_mdl, graph: nx.Graph, change: GraphChange, callback):
    global chat_limiter
    start = asyncio.get_running_loop().time()

    await thread_pool_exec(
        settings.docStoreConn.delete,
        {"knowledge_graph_kwd": ["graph", "subgraph"]},
        search.index_name(tenant_id),
        kb_id
    )

    if change.removed_nodes:
        await thread_pool_exec(
            settings.docStoreConn.delete,
            {"knowledge_graph_kwd": ["entity"], "entity_kwd": sorted(change.removed_nodes)},
            search.index_name(tenant_id),
            kb_id
        )

    if change.removed_edges:

        async def del_edges(from_node, to_node):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with chat_limiter:
                        await thread_pool_exec(
                            settings.docStoreConn.delete,
                            {"knowledge_graph_kwd": ["relation"], "from_entity_kwd": from_node, "to_entity_kwd": to_node},
                            search.index_name(tenant_id),
                            kb_id
                        )
                    return
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt
                        logging.warning(f"del_edges({from_node}, {to_node}) attempt {attempt + 1} failed: {e}, retrying in {wait}s")
                        await asyncio.sleep(wait)
                    else:
                        raise

        tasks = []
        for from_node, to_node in change.removed_edges:
            tasks.append(asyncio.create_task(del_edges(from_node, to_node)))

        try:
            await asyncio.gather(*tasks, return_exceptions=False)
        except Exception as e:
            logging.error(f"Error while deleting edges: {e}")
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    now = asyncio.get_running_loop().time()
    if callback:
        callback(msg=f"set_graph removed {len(change.removed_nodes)} nodes and {len(change.removed_edges)} edges from index in {now - start:.2f}s.")
    start = now

    chunks = [
        {
            "id": get_uuid(),
            "content_with_weight": json.dumps(nx.node_link_data(graph, edges="edges"), ensure_ascii=False),
            "knowledge_graph_kwd": "graph",
            "kb_id": kb_id,
            "source_id": graph.graph.get("source_id", []),
            "available_int": 0,
            "removed_kwd": "N",
        }
    ]

    # generate updated subgraphs
    for source in graph.graph["source_id"]:
        subgraph = graph.subgraph([n for n in graph.nodes if source in graph.nodes[n]["source_id"]]).copy()
        subgraph.graph["source_id"] = [source]
        for n in subgraph.nodes:
            subgraph.nodes[n]["source_id"] = [source]
        chunks.append(
            {
                "id": get_uuid(),
                "content_with_weight": json.dumps(nx.node_link_data(subgraph, edges="edges"), ensure_ascii=False),
                "knowledge_graph_kwd": "subgraph",
                "kb_id": kb_id,
                "source_id": [source],
                "available_int": 0,
                "removed_kwd": "N",
            }
        )

    tasks = []
    for ii, node in enumerate(change.added_updated_nodes):
        node_attrs = graph.nodes[node]
        tasks.append(asyncio.create_task(
            graph_node_to_chunk(kb_id, embd_mdl, node, node_attrs, chunks)
        ))
        if ii % 100 == 9 and callback:
            callback(msg=f"Get embedding of nodes: {ii}/{len(change.added_updated_nodes)}")
    try:
        await asyncio.gather(*tasks, return_exceptions=False)
    except Exception as e:
        logging.error(f"Error in get_embedding_of_nodes: {e}")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise

    tasks = []
    for ii, (from_node, to_node) in enumerate(change.added_updated_edges):
        edge_attrs = graph.get_edge_data(from_node, to_node)
        if not edge_attrs:
            continue
        tasks.append(asyncio.create_task(
            graph_edge_to_chunk(kb_id, embd_mdl, from_node, to_node, edge_attrs, chunks)
        ))
        if ii % 100 == 9 and callback:
            callback(msg=f"Get embedding of edges: {ii}/{len(change.added_updated_edges)}")
    try:
        await asyncio.gather(*tasks, return_exceptions=False)
    except Exception as e:
        logging.error(f"Error in get_embedding_of_edges: {e}")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise

    now = asyncio.get_running_loop().time()
    if callback:
        callback(msg=f"set_graph converted graph change to {len(chunks)} chunks in {now - start:.2f}s.")
    start = now

    enable_timeout_assertion = os.environ.get("ENABLE_TIMEOUT_ASSERTION")
    es_bulk_size = 4
    for b in range(0, len(chunks), es_bulk_size):
        timeout = 3 if enable_timeout_assertion else 30000000
        max_retries = 3
        for attempt in range(max_retries):
            task = asyncio.create_task(
                thread_pool_exec(
                    settings.docStoreConn.insert,
                    chunks[b : b + es_bulk_size],
                    search.index_name(tenant_id),
                    kb_id
                )
            )
            try:
                doc_store_result = await asyncio.wait_for(task, timeout=timeout)
                break
            except asyncio.TimeoutError:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logging.warning(f"Insert batch {b}/{len(chunks)} attempt {attempt + 1} timed out, retrying in {wait}s")
                    await asyncio.sleep(wait)
                else:
                    raise
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logging.warning(f"Insert batch {b}/{len(chunks)} attempt {attempt + 1} failed: {e}, retrying in {wait}s")
                    await asyncio.sleep(wait)
                else:
                    raise
        if b % 100 == es_bulk_size and callback:
            callback(msg=f"Insert chunks: {b}/{len(chunks)}")
        if doc_store_result:
            error_message = f"Insert chunk error: {doc_store_result}, please check log file and Elasticsearch/Infinity status!"
            raise Exception(error_message)
    now = asyncio.get_running_loop().time()
    if callback:
        callback(msg=f"set_graph added/updated {len(change.added_updated_nodes)} nodes and {len(change.added_updated_edges)} edges from index in {now - start:.2f}s.")