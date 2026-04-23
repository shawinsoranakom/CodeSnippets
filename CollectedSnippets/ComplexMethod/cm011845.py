def inner(
        *size,
        names=None,
        dtype=None,
        device=None,
        layout=None,
        pin_memory=False,
        memory_format=None,
    ):
        assert_nyi(names is None, "named tensors")
        assert_nyi(layout in (None, torch.strided), f"layout={layout}")
        assert_nyi(not memory_format, "memory_format")
        device = decode_device(device)
        dtype = dtype or torch.get_default_dtype()
        if len(size) == 1 and isinstance(size[0], (list, tuple, torch.Size)):
            size = tuple(size[0])
        # See https://github.com/pytorch/pytorch/issues/118102
        # All sizes at lowering time should be sympy.Symbol, not SymInt!
        for s in size:
            assert not isinstance(s, torch.SymInt)
        size = [sympy.expand(s) for s in size]
        full_pointwise = _full(fill_value, decode_device(device), dtype, size)

        if pin_memory:
            # Realize the buffer
            full_pointwise.realize()
            full_pointwise.data.data.get_layout().is_pinned = True

        return full_pointwise