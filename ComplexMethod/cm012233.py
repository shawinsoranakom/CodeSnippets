def apply_group_batch_fusion(graph: torch.fx.GraphModule, rule: GroupBatchFusionBase):
    stable_topological_sort(graph)  # type: ignore[arg-type]
    fused_set = OrderedSet[torch.fx.Node]()
    log_to_scuba = False

    for node in reversed(graph.nodes):  # type: ignore[arg-type]
        candidates = get_fusion_candidates(rule, node, fused_set)

        for key, candidate_nodes in candidates.items():
            if len(candidate_nodes) < rule.graph_search_options["min_fuse_set_size"]:
                continue

            for subset in find_independent_subset_greedy(
                candidate_nodes, rule.graph_search_options
            ):
                rule.fuse(graph, subset)
                fused_set.update(subset)
                log.debug(
                    f"{rule.__class__.__name__}: key = {key}; subset size = {len(list(subset))}"  # noqa: G004
                )
                log_to_scuba = True
    if log_to_scuba:
        from torch.fx._lazy_graph_module import _LazyGraphModule

        # Force graph to re-compile otherwise the output python code may be broken
        gm = graph._owning_module
        if isinstance(gm, _LazyGraphModule):
            _LazyGraphModule.recompile()
        else:
            assert isinstance(gm, torch.fx.GraphModule)
            gm.recompile()
        graph_str = gm.print_readable(
            print_output=False, include_stride=True, include_device=True
        )

        name = f"optimus_{str(rule.__class__.__name__)}"
        if "MTIA" in name:
            name = f"cff_{str(rule.__class__.__name__)}"
        trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": name,
                "encoding": "string",
            },
            payload_fn=lambda: graph_str,
        )