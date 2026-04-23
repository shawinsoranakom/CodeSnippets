def ban_recomputation_if_allowed(node: fx.Node, reason: str = "") -> bool:
        if op_types.is_view(node):
            return False
        if node in dont_ban:
            # collectives are *always* banned from recompute, overriding `dont_ban`
            # (in particular, the activation memory budget logic is not allowed to recompute collectives)
            is_collective = (
                isinstance(node.target, torch._ops.OpOverload)
                and node.target.namespace == "_c10d_functional"
            )
            if config.unsafe_allow_optimization_of_collectives or not is_collective:
                return False
        # This bans recomputation of the node unless we've been forced not to by
        # user annotation
        if must_recompute(node):
            return False

        if "val" in node.meta and isinstance(node.meta["val"], torch.SymFloat):
            return False
        banned_nodes.add(node)
        # A node will only ever be recomputed if there is a path from an
        # ancestor of this node to the backwards path through this node that
        # doesn't go through any saved value. If this node is saved, then that
        # condition is not possible.
        nx_graph.add_edge(
            "source",
            node.name + "_in",
            capacity=math.inf,
            reason=f"cannot recompute: {reason}" if reason else "cannot recompute",
        )
        return True