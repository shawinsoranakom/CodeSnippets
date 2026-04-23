def _validate_input(cfn, lxs, d, r, cm):
        # Basic arguments check
        if not callable(cfn):
            raise ValueError(f"Combine_fn must be a callable, but got {cfn}")
        if not isinstance(d, int):
            raise ValueError("Dim must be an int, but got " + str(type(d)))
        if not isinstance(r, bool):
            raise RuntimeError("Reverse must be a bool, but got " + str(type(r)))
        if cm not in ["pointwise", "generic"]:
            raise ValueError(
                f"Combine_mode must either 'pointwise' or 'generic', but got {cm}"
            )
        if cm == "pointwise" and not all(l.device.type in ("cuda", "xpu") for l in lxs):
            raise ValueError(
                "For combine_mode='pointwise', all input tensors need to be on CUDA or XPU"
            )

        # Checks for xs
        if len(lxs) == 0:
            raise ValueError("Expected at least 1 xs leaf")
        if any(not isinstance(x, torch.Tensor) for x in lxs):
            raise ValueError("xs leaves must be a Tensor")
        if any(x.is_sparse for x in lxs):
            raise ValueError(
                "xs leaves must dense Tensors, consider using `to_dense()`"
            )
        if any(x.ndim <= d for x in lxs):
            raise ValueError(
                "All xs leaves must at least have 'dim' number of dimensions and scan dimension > 0"
            )
        if any(x.shape[d] == 0 for x in lxs):
            raise ValueError(
                "All xs leaves must at least have 'dim' number of dimensions and scan dimension > 0"
            )