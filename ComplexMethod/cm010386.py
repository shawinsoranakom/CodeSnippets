def _validate_input(cfn, lxs, linit, d, r):
        # Basic arguments check
        if not callable(cfn):
            raise RuntimeError(f"Combine_fn must be a callable, but got {cfn}")
        if not isinstance(d, int):
            raise RuntimeError("Dim must be an int, but got " + str(type(d)))
        if not isinstance(r, bool):
            raise RuntimeError("Reverse must be a bool, but got " + str(type(r)))

        # Checks for init
        if len(linit) == 0:
            raise RuntimeError("scan() operator requires init leaves.")
        for x in linit:
            if not isinstance(x, torch.Tensor):
                raise RuntimeError(f"All init leaves must be a Tensor but got {x}")

        # Checks for xs
        for x in lxs:
            if not isinstance(x, torch.Tensor):
                raise RuntimeError(f"All xs leaves must be a Tensor but got {x}")
        if any(x.ndim <= d for x in lxs):
            raise RuntimeError(
                "All xs leaves must at least have 'dim' number of dimensions and scan dimension > 0"
            )
        if any(x.shape[d] == 0 for x in lxs):
            raise RuntimeError(
                "All xs leaves must at least have 'dim' number of dimensions and scan dimension > 0"
            )