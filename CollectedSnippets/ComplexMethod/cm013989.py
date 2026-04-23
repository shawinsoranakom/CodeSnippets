def _graph_device_type(graph: Graph | None) -> str:
    if graph is None:
        return "cpu"

    def _device_type(x: Any) -> str:
        if isinstance(x, torch.device):
            return x.type
        if isinstance(x, torch.Tensor):
            return x.device.type
        return "cpu"

    def _flatten_meta(node: Node, key: str) -> list[Any]:
        if key not in node.meta:
            return []
        flat, _ = tree_flatten(node.meta[key])
        return flat

    for node in graph.nodes:
        for key in ("val", "example_value"):
            for obj in _flatten_meta(node, key):
                return _device_type(obj)

        # Check for device conversions
        if node.op == "call_method":
            for gpu in ["cuda", "xpu"]:
                if node.target == gpu:
                    return gpu
                if node.target == "to" and gpu in node.args:
                    return gpu

        # Check args/kwargs for non-CPU device specs
        flat_args, _ = tree_flatten((node.args, node.kwargs))
        for obj in flat_args:
            return _device_type(obj)
    return "cpu"