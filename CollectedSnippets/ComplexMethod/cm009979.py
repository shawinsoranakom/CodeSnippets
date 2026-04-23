def create(
        h: Any, ensure_batched: bool = True, ensure_present: bool = True
    ) -> TensorInfo:
        from . import Dim, DimEntry, Tensor

        if Tensor.check_exact(h):
            # functorch Tensor with first-class dimensions
            return TensorInfo(
                h._get_tensor(),
                h._get_levels(),
                h._get_has_device(),
                h._get_batchtensor() if ensure_batched else None,
            )
        elif Dim.check_exact(h):
            # For Dim objects, only get range/batchtensor if needed and dimension is bound
            tensor = h._get_range() if h.is_bound else None
            batchtensor = (
                h._get_batchtensor() if ensure_batched and h.is_bound else None
            )
            return TensorInfo(
                tensor,
                [DimEntry(h)],
                False,
                batchtensor,
            )
        elif isinstance(h, torch.Tensor):
            # Plain torch tensor - create positional levels
            levels = []
            for i in range(-h.dim(), 0):
                levels.append(DimEntry(i))
            return TensorInfo(h, levels, True, h)
        else:
            if ensure_present:
                raise ValueError("expected a tensor object")
            return TensorInfo(None, [], False, None)