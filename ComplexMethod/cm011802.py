def as_strided(x, size, stride, storage_offset=None):
    new_device = None
    new_dtype = None
    if isinstance(x, TensorBox) and isinstance(x.data, ir.BaseView):
        # Note: Merging views
        # When we use as_strided, we can rewrite the size/stride/offset
        # of the incoming buffer x. If x is a view, we would overwrite
        # its metadata. Except for dtype, which we need to propagate.

        # Technically device is not needed because it is not possible
        # to have a cross-device view today.
        new_device = x.get_device()
        new_dtype = x.dtype
        x = x.data.unwrap_view()
    x.realize()
    if not ir.is_storage_and_layout(x):
        raise NotImplementedError(f"unrealized as_strided({x}, ...)")
    storage, old_layout = ir.as_storage_and_layout(x)
    new_layout = ir.FixedLayout(
        new_device if new_device else old_layout.device,
        new_dtype if new_dtype else old_layout.dtype,
        [sympy.expand(s) for s in size],
        [sympy.expand(s) for s in stride],
        sympy.expand(storage_offset or 0),
    )
    return TensorBox(ir.ReinterpretView(data=storage, layout=new_layout))