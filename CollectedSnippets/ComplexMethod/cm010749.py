def get_node_weight(
        node: fx.Node, static_lifetime_input_nodes: OrderedSet[fx.Node]
    ) -> tuple[float, str | None]:
        """Returns (weight, cannot_save_reason).

        cannot_save_reason is None for finite weights, or a string explaining
        why the node cannot be saved for infinite weights.
        """
        if (
            config.treat_parameters_as_free_to_save
            and node in static_lifetime_input_nodes
        ):
            return 0, None
        mem_sz = _size_of(node)
        if config.recompute_views and op_types.is_view(node):
            # If `config.recompute_views=True`, we don't save views. This is generally
            # a good idea since views are free to recompute, and it makes it a bit simpler
            # to analyze.
            # NB: If they're not free to recompute (e.g. nested tensors)... I
            # think we should modify checks for view_ops to `is_view` and check
            # that. Basically, with nested tensors, `aten.view` is not a "view
            # op".
            return math.inf, "view op (recompute_views=True)"

        if isinstance(node.meta["val"], py_sym_types):
            # We never want to save symfloats
            if not isinstance(node.meta["val"], torch.SymInt):
                return INT_INF, "SymFloat (non-SymInt symbolic value)"

        # Heuristic to bias towards nodes closer to the backwards pass
        # Complete guess about current value
        mem_sz = int(
            # pyrefly: ignore [missing-attribute]
            mem_sz * (1.1 ** max(min(node.dist_from_bw, 100), 1))
        )
        if is_materialized(node):
            return mem_sz, None
        else:
            return mem_sz * 2, None