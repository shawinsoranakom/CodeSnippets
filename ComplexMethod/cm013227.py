def __new__(cls, a, b, outer_size=None, outer_stride=None, *, requires_grad=None):
        if outer_size is None:
            outer_size = a.size()
        if outer_stride is None:
            outer_stride = a.stride()

        if not (
            a.device == b.device
            and a.layout == b.layout
            and a.requires_grad == b.requires_grad
            and a.dtype == b.dtype
        ):
            raise AssertionError(
                "Expected a and b to have same device, layout, requires_grad, and dtype"
            )
        # I guess it would be more accurate to represent the shape as torch.cat(a, b).shape
        shape = outer_size
        kwargs = {}
        kwargs["strides"] = outer_stride
        kwargs["storage_offset"] = a.storage_offset()
        kwargs["device"] = a.device
        kwargs["layout"] = a.layout
        kwargs["requires_grad"] = requires_grad or a.requires_grad
        kwargs["dtype"] = a.dtype
        out = torch.Tensor._make_wrapper_subclass(cls, shape, **kwargs)

        if a.shape != b.shape:
            raise AssertionError(
                f"Expected a.shape == b.shape, got {a.shape} != {b.shape}"
            )
        if a.stride() != b.stride():
            raise AssertionError(
                f"Expected a.stride() == b.stride(), got {a.stride()} != {b.stride()}"
            )
        if a.storage_offset() != b.storage_offset():
            raise AssertionError(
                f"Expected a.storage_offset() == b.storage_offset(), "
                f"got {a.storage_offset()} != {b.storage_offset()}"
            )
        return out