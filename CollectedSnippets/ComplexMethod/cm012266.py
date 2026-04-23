def _populate_node_meta(
    bucket_nodes: list[torch.fx.Node], new_nodes: list[torch.fx.Node]
):
    if bucket_nodes:
        for n in new_nodes:
            # For the following keys, we only store the information of the first node so
            # gm.print_readable shows some information
            # Full information are stored in "bucketing_{key}_sources"
            for key, default in [
                ("nn_module_stack", ""),
                ("fwd_nn_module_stack", ""),
                ("stack_trace", ""),
                ("custom", {}),
            ]:
                n.meta[key] = bucket_nodes[0].meta.get(key, default)

                # Collect sources from all bucket nodes for this metadata key, for debugging purposes only
                bucketing_sources_key = f"bucketing_{key}_sources"
                # Use set to remove duplicates
                if key == "stack_trace":
                    sources = OrderedSet(
                        [
                            node.meta.get(key, default)
                            for node in bucket_nodes
                            if node.meta.get(key, default)
                        ]
                    )
                else:
                    # type might not be hashable
                    sources = [
                        node.meta.get(key, default)
                        for node in bucket_nodes
                        if node.meta.get(key, default)
                    ]
                n.meta[bucketing_sources_key] = sources

            # used by inductor provenance tracking
            n.meta["from_node"] = [
                NodeSource(
                    original_node,
                    "bucketing_pass",
                    [NodeSourceAction.CREATE, NodeSourceAction.REPLACE],
                )
                for original_node in bucket_nodes
            ]