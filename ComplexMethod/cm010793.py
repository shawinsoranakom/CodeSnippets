def offload_activation_fw_async(graph: fx.Graph) -> None:
    """Insert async CPU offload operations in the forward pass graph.

    Uses ao.offload + ao.wait_tensor ops which encapsulate stream management
    internally, producing a clean 2-node IR per offloaded tensor.
    """

    op_types: OpTypes = get_default_op_list()

    output_node: fx.Node = graph.find_nodes(op="output")[0]
    # pyrefly: ignore [bad-assignment]
    fwd_outputs: tuple[fx.Node, ...] = output_node.args[
        0
    ]  # pyrefly: ignore [bad-assignment]
    node_to_offload: dict[fx.Node, fx.Node] = dict()
    node_to_index: dict[fx.Node, int] = {
        node: idx for idx, node in enumerate(graph.nodes)
    }

    if not any(n.meta.get("saved_for_offloading", False) for n in fwd_outputs):
        return

    for node in fwd_outputs:
        if node.meta.get("saved_for_offloading", False) is False:
            continue

        if all_effective_users := _find_all_effective_users(node, op_types):
            last_user = max(all_effective_users, key=lambda n: node_to_index[n])
        else:
            last_user: fx.Node = node

        with graph.inserting_after(last_user):
            offload_node: fx.Node = graph.call_function(
                torch.ops.ao.offload.default,
                args=(node,),
                name=f"async_{CPU_OFFLOAD_PREFIX}{node.name}",
            )
            offload_node.meta["val"] = node.meta["val"].to(torch.device("cpu"))
            offload_node.meta["tensor_meta"] = extract_tensor_metadata(
                offload_node.meta["val"]
            )
        # The keepalive=node arg extends the GPU tensor's lifetime in the
        # graph so the allocator doesn't reclaim it before the async D2H
        # copy completes.
        with graph.inserting_after(offload_node):
            wait_node: fx.Node = graph.call_function(
                torch.ops.ao.wait_tensor.default,
                args=(offload_node, node),
                name=CPU_OFFLOAD_PREFIX + str(node.name),
            )
            wait_node.meta["val"] = offload_node.meta["val"]
            wait_node.meta["tensor_meta"] = offload_node.meta["tensor_meta"]

        node_to_offload[node] = wait_node

    output_node.update_arg(
        0, tuple(node_to_offload.get(node, node) for node in fwd_outputs)
    )