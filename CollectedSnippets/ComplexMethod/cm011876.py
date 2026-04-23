def _transfer_meta(
    new_meta: dict[str, Any], old_node: torch.fx.Node, pass_name: str = ""
) -> None:
    from torch.fx.traceback import NodeSource, NodeSourceAction

    # Transfer metadata after pattern matching occurs.
    # Copies _COPY_META_FIELDS, stack_trace, and (if missing) val/tensor_meta.
    if config.trace.provenance_tracking_level == 1:
        new_from_node = new_meta.get("from_node", []).copy()
        new_from_node.append(NodeSource(old_node, pass_name, NodeSourceAction.REPLACE))
        new_meta.update(
            (k, v)
            for k, v in old_node.meta.items()
            if k in torch.fx.proxy._COPY_META_FIELDS
        )
        new_meta["from_node"] = new_from_node
    else:
        new_meta.update(
            (k, v)
            for k, v in old_node.meta.items()
            if k in torch.fx.proxy._COPY_META_FIELDS
        )
    if "stack_trace" in old_node.meta:
        new_meta["stack_trace"] = old_node.meta["stack_trace"]
    # Copy val/tensor_meta only when the new node doesn't already have them
    # (e.g. from tracing the replacement graph). Don't overwrite if present
    # since the replacement's own val is more accurate.
    if "val" not in new_meta and "val" in old_node.meta:
        new_meta["val"] = old_node.meta["val"]
    if "tensor_meta" not in new_meta and "tensor_meta" in old_node.meta:
        new_meta["tensor_meta"] = old_node.meta["tensor_meta"]