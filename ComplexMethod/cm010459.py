def __new__(
        cls,
        values,
        offsets,
        *,
        lengths=None,
        **kwargs,
    ):
        ks = DispatchKeySet(DispatchKey.NestedTensor)
        ks = ks.add(DispatchKey.AutogradNestedTensor)

        # Only support jagged for now.
        if offsets is None:
            raise AssertionError("offsets must not be None")
        if offsets.ndim != 1:
            raise AssertionError(f"offsets must be 1D, but got {offsets.ndim}D")
        if isinstance(values, NestedTensor):
            raise AssertionError("values must not be a NestedTensor")
        if values.device != offsets.device:
            raise AssertionError(
                f"values and offsets must be on the same device, but got "
                f"values.device={values.device} and offsets.device={offsets.device}"
            )

        # Query cache for the symint associated with offsets or lengths
        # (create a new one if needed).
        ragged_source = offsets if lengths is None else lengths
        ragged_size = get_tensor_symint(ragged_source, coeff=1)
        _ragged_idx = kwargs.get("_ragged_idx", 1)
        B = offsets.shape[0] - 1
        if lengths is not None:
            if B != lengths.shape[0]:
                raise AssertionError(
                    f"offsets and lengths batch sizes must match: "
                    f"offsets.shape[0] - 1 = {B}, lengths.shape[0] = {lengths.shape[0]}"
                )

        # subtract 1 to convert to values dim space
        r = _ragged_idx - 1
        _size = (B, *values.shape[:r], ragged_size, *values.shape[r + 1 :])
        stride = values.stride()
        _strides = (ragged_size * stride[r], *stride)

        r = torch.Tensor._make_wrapper_subclass(
            cls,
            _size,
            _strides,
            0,
            torch.contiguous_format,
            values.dtype,
            torch.jagged,
            values.device,
            False,
            kwargs.get("requires_grad", False),
            "sizes",
            False,
            True,  # dispatch_layout
            ks,
            # don't try to calculate storage based on non-zero size
            storage_size=values.untyped_storage().size(),
        )
        r._ragged_idx = _ragged_idx
        r._size = _size
        r._strides = _strides

        return r