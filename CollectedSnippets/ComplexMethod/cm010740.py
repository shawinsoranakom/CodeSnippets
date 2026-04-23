def cleanup_recompute_tags(
    joint_module: fx.GraphModule, *, is_default_partition: bool
) -> fx.GraphModule:
    """
    If there are two consecutive checkpointed blocks with no operator in
    between, we would still want to stash the tensor at the boundary of
    checkpointed blocks. The following pass makes the last output node
    non-recomputable to allow for that.
    """
    for node in joint_module.graph.nodes:
        if must_recompute(node):
            for user in node.users:
                if (
                    must_recompute(user)
                    and "ac_graph_id" in user.meta
                    and "ac_graph_id" in node.meta
                    and user.meta["ac_graph_id"] > node.meta["ac_graph_id"]
                ):
                    node.meta["recompute"] = CheckpointPolicy.MUST_SAVE
            if node.meta.get("has_backward_hook", False) and not any(
                must_recompute(user) for user in node.users
            ):
                # If node is AC region output and has a backward hook on it, we intentionally choose to save it.
                # This is to work around circular dependencies in Traceable FSDP2+AC.
                # Example:
                # ```
                # out = fully_shard(utils.checkpoint(module))(x)
                # norm_out = layer_norm(out)
                # ```
                # Here there is a circular dependency:
                # 1. In backward, grad_input of layer_norm aka. `out_grad` is actually dependent on `out`.
                # 2. `out` depends on `out`'s backward hook created by FSDP2 (which does all-gather for `module` weights)
                #    in order to be recomputed.
                # 3. `out`'s backward hook, as is the case for all eager backward hooks, depends on `out_grad`
                #    -> circular dependency with (1)!
                #
                # Solution: check whether `out` has a backward hook, and if so, intentionally save `out`
                # in forward graph outputs. With this, we can break the above circular dependency.
                node.meta["recompute"] = CheckpointPolicy.MUST_SAVE
        elif (
            "ac_graph_id" not in node.meta
            and any(must_recompute(user) for user in node.users)
            and not (
                # Avoid saving getitem nodes which are not labeled with "ac_graph_id"
                is_getitem_of_multi_output(node) and "ac_graph_id" in node.args[0].meta
            )
            and is_default_partition
        ):
            # This node is not part of the AC region and a user is marked as recompute.
            # This means it's an input to the AC region and we should save it.
            # For ease of landing, gate this to default partitioner only, but we should think
            # about flipping the switch in general as well.
            node.meta["recompute"] = CheckpointPolicy.MUST_SAVE
    return joint_module