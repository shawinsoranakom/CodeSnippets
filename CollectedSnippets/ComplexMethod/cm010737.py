def _size_of(node: fx.Node) -> int:
    def object_nbytes(x: object) -> int:
        if not isinstance(x, torch.Tensor):
            return 0
        return _tensor_nbytes(optimization_hint(x.numel(), fallback=4096), x.dtype)

    if "val" in node.meta:
        val = node.meta["val"]
        if isinstance(val, py_sym_types):
            return 1
        # NB: The fallback values here are meaningless, maybe we should respect
        # torch._inductor.config.unbacked_symint_fallback (but this is a
        # layering violation)
        elif isinstance(val, (list, tuple)):
            return sum(object_nbytes(n) for n in val)
        elif isinstance(val, dict):
            return sum(object_nbytes(n) for _, n in val.items())
        elif isinstance(val, torch.Tensor):
            return object_nbytes(val)

        raise RuntimeError(f"Unknown metadata type {type(val)} on node {node}")
    if node.op == "get_attr" or node.target is torch.ops.aten._assert_scalar.default:
        return 0
    raise RuntimeError(
        f"Node {node} didn't have `val` metadata; we should always have `val` metadata on the nodes."
    )