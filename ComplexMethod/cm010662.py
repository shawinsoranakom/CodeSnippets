def analyze_ts_result_with_export_result(export, trace):
    import torch.utils._pytree as pytree

    flat_export = pytree.tree_leaves(export)
    flat_trace = pytree.tree_leaves(trace)

    for orig, loaded in zip(flat_export, flat_trace):
        if orig.layout != loaded.layout:
            return False
        # mkldnn is not supported for torch.allclose
        if orig.layout == torch._mkldnn:  # type: ignore[attr-defined]
            return True
        if type(orig) is not type(loaded):
            return False

        if isinstance(orig, torch._subclasses.FakeTensor):
            # Skip for FakeTensor.
            return True
        elif isinstance(orig, torch.Tensor):
            if orig.dtype != loaded.dtype:
                return False
            if not torch.allclose(orig, loaded):
                return False
        else:
            if orig != loaded:
                return False
    return True