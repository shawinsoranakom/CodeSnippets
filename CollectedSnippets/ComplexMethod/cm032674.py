async def rebuild_graph(tenant_id, kb_id, exclude_rebuild=None):
    graph = nx.Graph()
    flds = ["knowledge_graph_kwd", "content_with_weight", "source_id"]
    bs = 256
    for i in range(0, 1024 * bs, bs):
        es_res = await thread_pool_exec(
            settings.docStoreConn.search,
            flds, [], {"kb_id": kb_id, "knowledge_graph_kwd": ["subgraph"]},
            [], OrderByExpr(), i, bs, search.index_name(tenant_id), [kb_id]
        )
        # tot = settings.docStoreConn.get_total(es_res)
        es_res = settings.docStoreConn.get_fields(es_res, flds)

        if len(es_res) == 0:
            break

        for id, d in es_res.items():
            assert d["knowledge_graph_kwd"] == "subgraph"
            if isinstance(exclude_rebuild, list):
                if sum([n in d["source_id"] for n in exclude_rebuild]):
                    continue
            elif exclude_rebuild in d["source_id"]:
                continue

            next_graph = json_graph.node_link_graph(json.loads(d["content_with_weight"]), edges="edges")
            merged_graph = nx.compose(graph, next_graph)
            merged_source = {n: graph.nodes[n]["source_id"] + next_graph.nodes[n]["source_id"] for n in graph.nodes & next_graph.nodes}
            nx.set_node_attributes(merged_graph, merged_source, "source_id")
            if "source_id" in graph.graph:
                merged_graph.graph["source_id"] = graph.graph["source_id"] + next_graph.graph["source_id"]
            else:
                merged_graph.graph["source_id"] = next_graph.graph["source_id"]
            graph = merged_graph

    if len(graph.nodes) == 0:
        return None
    graph.graph["source_id"] = sorted(graph.graph["source_id"])
    return graph