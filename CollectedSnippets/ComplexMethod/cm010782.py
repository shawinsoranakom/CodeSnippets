def _convert_node_to_placeholder(
    graph: fx.Graph, node: fx.Node, inps: list[torch.Tensor]
) -> bool:
    if node.op == "output" or node.op == "placeholder":
        return False

    if is_load_tensor_node(node):
        return False

    concrete_val = node.meta.get("concrete_value", None)

    if isinstance(concrete_val, torch.Tensor):
        node.op = "placeholder"
        node.target = node.name
        node.args = ()
        node.kwargs = {}

        inps.append(concrete_val)
        return True

    elif concrete_val is None:
        return False

    elif concrete_val is is_tuple:
        r = False
        for tuple_user in list(node.users):
            r = _convert_node_to_placeholder(graph, tuple_user, inps) or r
        # NB: We must not erase the node at this point, because
        # we are iterating over the nodes and this would change
        # the iteration order
        # graph.erase_node(node)
        return r

    elif isinstance(concrete_val, LoadTensorMeta):
        node.op = "call_function"
        node.target = torch.ops.debugprims.load_tensor.default
        node.args = (
            os.path.join("eager", node.name),
            concrete_val.size,
            concrete_val.stride,
        )
        node.kwargs = {
            "device": concrete_val.device,
            "dtype": concrete_val.dtype,
        }
        return True

    return False