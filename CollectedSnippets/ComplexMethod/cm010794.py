def reload_activation_bw_async(graph: fx.Graph) -> None:
    """Insert async GPU reload operations in the backward pass graph.

    Uses ao.reload + ao.wait_tensor ops which encapsulate stream management internally,
    producing a clean 2-node IR per reloaded tensor.
    """

    node_to_index: dict[fx.Node, int] = {
        node: idx for idx, node in enumerate(graph.nodes)
    }

    nodes_to_reload = [
        n
        for n in graph.find_nodes(op="placeholder")
        if n.meta.get("saved_for_offloading", False)
    ]
    if not nodes_to_reload:
        return

    for node in nodes_to_reload:
        if not node.users:
            raise RuntimeError(
                f"Offloaded tensor {node.name} has no users in the backward graph"
            )
        insert_point: fx.Node = min(node.users.keys(), key=lambda n: node_to_index[n])

        original_device: torch.device = node.meta["original_device"]
        with graph.inserting_before(insert_point):
            reload_node: fx.Node = graph.call_function(
                torch.ops.ao.reload.default,
                args=(node, original_device),
                name=f"async_{str(node.name).replace(CPU_OFFLOAD_PREFIX, GPU_RELOAD_PREFIX)}",
            )
            reload_node.meta["val"] = node.meta["val"].to(original_device)
            reload_node.meta["tensor_meta"] = extract_tensor_metadata(
                reload_node.meta["val"]
            )
            wait_node: fx.Node = graph.call_function(
                torch.ops.ao.wait_tensor.default,
                args=(reload_node,),
                name=str(node.name).replace(CPU_OFFLOAD_PREFIX, GPU_RELOAD_PREFIX),
            )
            wait_node.meta["val"] = reload_node.meta["val"]
            wait_node.meta["tensor_meta"] = reload_node.meta["tensor_meta"]

        for user in list(node.users.keys()):
            if user != reload_node:
                user.replace_input_with(node, wait_node)