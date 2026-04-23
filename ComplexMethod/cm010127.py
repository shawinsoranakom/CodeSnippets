def _collect_param_buffer_metadata(mod: torch.fx.GraphModule) -> dict[str, Any]:
    """
    Param/buffer metadata needs to be saved before lowering to aten IR
    because aten IR lifts them, as a result, automatic preservation doesn't work.
    This is intended to be called on the strict mode tracing right before lowering to
    aten IR OR run_decomposition pass.
    """
    params_buffers_to_node_meta = {}

    def _getattr(model: torch.fx.GraphModule, attr_name: str):
        *prefix, field = attr_name.split(".")
        t = model
        for item in prefix:
            t = getattr(t, item, None)  # type: ignore[assignment]
            if t is None:
                raise AssertionError(f"attribute {item!r} not found in path")

        return getattr(t, field)

    for node in mod.graph.nodes:
        target = node.target
        meta = node.meta
        if node.op == "call_module":
            submodule = _getattr(mod, target)
            if isinstance(submodule, torch.nn.Module):
                for name, _ in submodule.named_parameters(
                    recurse=True, remove_duplicate=False
                ):
                    params_buffers_to_node_meta[target + "." + name] = meta

                for name, _ in submodule.named_buffers(
                    recurse=True, remove_duplicate=False
                ):
                    params_buffers_to_node_meta[target + "." + name] = meta

        if node.op == "get_attr":
            submodule = _getattr(mod, target)
            if not isinstance(submodule, torch.fx.GraphModule):
                params_buffers_to_node_meta[target] = meta

        # If the call_function uses param as input, we also need to update params' meta
        # with this call_function node's meta.
        # This is basically the same flow as torch.fx.traceback.preserve_meta()
        if node.op == "call_function" and not isinstance(
            node.target, torch._ops.HigherOrderOperator
        ):
            for arg in node._input_nodes:
                if arg.op == "get_attr":
                    for entry in torch.fx.proxy._COPY_META_FIELDS:
                        #  the custom field should not be copied
                        if entry == "custom":
                            continue
                        if entry in meta:
                            params_buffers_to_node_meta[arg.target][entry] = meta[entry]

    return params_buffers_to_node_meta