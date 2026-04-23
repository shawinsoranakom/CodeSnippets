def arange(g: jit_utils.GraphContext, *args):
    def _get_arange_dtype(dtype):
        dtype = symbolic_helper._maybe_get_const(dtype, "i")
        return dtype

    if len(args) == 2 and all(isinstance(val, int) for val in args):
        # aten::arange(Scalar start, Scalar end)
        dtype = torch.int64
        # Start index.
        start = g.op(
            "Constant",
            value_t=torch.tensor(args[0], dtype=dtype),
        )
        # End (exclusive) index.
        end = g.op(
            "Constant",
            value_t=torch.tensor(args[1], dtype=dtype),
        )
        # Step size from start to end indexes.
        delta_default = g.op(
            "Constant",
            value_t=torch.tensor(1, dtype=dtype),
        )
        return g.op("Range", start, end, delta_default)
    elif len(args) == 2 or len(args) == 5:
        if len(args) == 2:
            # aten::arange(Scalar end, Tensor out)
            dtype = None
        else:
            # aten::arange(Scalar end, ScalarType dtype, Layout, Device, bool pin_memory)
            dtype = _get_arange_dtype(args[1])
        type_, end, start, step = symbolic_helper._arange_cast_helper(
            g, end=args[0], dtype=dtype
        )
        start_default = g.op(
            "Constant",
            value_t=torch.tensor(0, dtype=type_.dtype()),
        )
        delta_default = g.op(
            "Constant",
            value_t=torch.tensor(1, dtype=type_.dtype()),
        )
        # pyrefly: ignore [bad-argument-type]
        return g.op("Range", start_default, end, delta_default)
    elif len(args) == 4 or len(args) == 7:
        if len(args) == 4:
            # aten::arange(Scalar start, Scalar end, Scalar step, Tensor out)
            dtype = None
        else:
            # aten::arange(Scalar start, Scalar end, Scalar step, ScalarType dtype, Layout, Device, bool pin_memory)
            dtype = _get_arange_dtype(args[3])
        _, end, start, step = symbolic_helper._arange_cast_helper(
            g, start=args[0], end=args[1], step=args[2], dtype=dtype
        )
        # pyrefly: ignore [bad-argument-type]
        return g.op("Range", start, end, step)
    elif len(args) == 6:
        # aten::arange(Scalar start, Scalar end, ScalarType dtype, Layout, Device, bool pin_memory)
        dtype = _get_arange_dtype(args[2])
        type_, end, start, step = symbolic_helper._arange_cast_helper(
            g, start=args[0], end=args[1], dtype=dtype
        )
        delta_default = g.op(
            "Constant",
            value_t=torch.tensor(1, dtype=type_.dtype()),
        )
        # pyrefly: ignore [bad-argument-type]
        return g.op("Range", start, end, delta_default)
    else:
        return symbolic_helper._unimplemented(
            "aten::arange", f"with {len(args)} arguments"
        )