def arange(g: jit_utils.GraphContext, *args):
    def _get_arange_dtype(dtype):
        dtype = symbolic_helper._maybe_get_const(dtype, "i")
        return dtype

    def _float_step_convert(range_tensor):
        if symbolic_helper._is_fp(range_tensor):
            range_tensor = g.op(
                "Cast",
                g.op("Ceil", range_tensor),
                to_i=_type_utils.JitScalarType.INT64.onnx_type(),
            )
        return range_tensor

    if len(args) == 2 or len(args) == 5:
        if len(args) == 2:
            # aten::arange(Scalar end, Tensor out)
            dtype = None
        else:
            # aten::arange(Scalar end, ScalarType dtype, Layout, Device, bool pin_memory)
            dtype = _get_arange_dtype(args[1])
        dtype, end, start, step = symbolic_helper._arange_cast_helper(
            g, end=args[0], dtype=dtype
        )
        end = symbolic_helper._unsqueeze_helper(g, end, [0])
        range_tensor = _float_step_convert(end)
        arange_tensor = symbolic_helper._squeeze_helper(
            g, nonzero(g, ones(g, range_tensor, dtype, None, None)), [1]
        )
        return g.op(
            "Cast", arange_tensor, to_i=_type_utils.JitScalarType(dtype).onnx_type()
        )
    elif len(args) == 4 or len(args) == 7:
        if len(args) == 4:
            # aten::arange(Scalar start, Scalar end, Scalar step, Tensor out)
            dtype = None
        else:
            # aten::arange(Scalar start, Scalar end, Scalar step, ScalarType dtype, Layout, Device, bool pin_memory)
            dtype = _get_arange_dtype(args[3])
        dtype, end, start, step = symbolic_helper._arange_cast_helper(
            g, start=args[0], end=args[1], step=args[2], dtype=dtype
        )
        step = symbolic_helper._unsqueeze_helper(g, step, [0])
        end = symbolic_helper._unsqueeze_helper(g, end, [0])
        start = symbolic_helper._unsqueeze_helper(g, start, [0])
        range_tensor = _float_step_convert(g.op("Div", g.op("Sub", end, start), step))
        arange_tensor = symbolic_helper._squeeze_helper(
            g, nonzero(g, ones(g, range_tensor, None, None, None)), [1]
        )
        arange_tensor = g.op("Add", g.op("Mul", arange_tensor, step), start)
        return g.op(
            "Cast", arange_tensor, to_i=_type_utils.JitScalarType(dtype).onnx_type()
        )
    elif len(args) == 6:
        # aten::arange(Scalar start, Scalar end, ScalarType dtype, Layout, Device, bool pin_memory)
        dtype = _get_arange_dtype(args[2])
        dtype, end, start, step = symbolic_helper._arange_cast_helper(
            g, start=args[0], end=args[1], dtype=dtype
        )
        end = symbolic_helper._unsqueeze_helper(g, end, [0])
        start = symbolic_helper._unsqueeze_helper(g, start, [0])
        range_tensor = _float_step_convert(g.op("Sub", end, start))
        arange_tensor = g.op(
            "Add",
            symbolic_helper._squeeze_helper(
                g, nonzero(g, ones(g, range_tensor, dtype, *(args[3:]))), [1]
            ),
            start,
        )
        return g.op(
            "Cast", arange_tensor, to_i=_type_utils.JitScalarType(dtype).onnx_type()
        )

    return symbolic_helper._unimplemented("aten::arange", f"with {len(args)} arguments")