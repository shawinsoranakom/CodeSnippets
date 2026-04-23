def _linalg_vector_norm_helper(
    g: jit_utils.GraphContext,
    self: torch._C.Value,
    ord: float,
    dim: Sequence[int] | None,
    keepdim: bool,
    dtype: torch._C.Value,
):
    axes = None
    # Conditions based on https://pytorch.org/docs/stable/generated/torch.linalg.vector_norm.html
    if _is_none(dim):
        self = _reshape_helper(g, self, [-1])
        keepdim = False
    elif g.opset >= 18:
        axes = g.op("Constant", value_t=torch.tensor(dim, dtype=torch.long))

    if ord == math.inf:
        if g.opset < 18:
            result = g.op(
                "ReduceMax", g.op("Abs", self), axes_i=dim, keepdims_i=keepdim
            )
        else:
            if axes is None:
                result = g.op("ReduceMax", g.op("Abs", self), keepdims_i=keepdim)
            else:
                result = g.op("ReduceMax", g.op("Abs", self), axes, keepdims_i=keepdim)
    elif ord == -math.inf:
        if g.opset < 18:
            result = g.op(
                "ReduceMin", g.op("Abs", self), axes_i=dim, keepdims_i=keepdim
            )
        else:
            if axes is None:
                result = g.op("ReduceMin", g.op("Abs", self), keepdims_i=keepdim)
            else:
                result = g.op("ReduceMin", g.op("Abs", self), axes, keepdims_i=keepdim)
    elif ord == 0:
        if g.opset < 11:
            return _onnx_opset_unsupported_detailed(
                "linalg_vector_norm", 9, 11, "ord=0 not supported", self
            )
        else:
            if dim is None:
                self = _reshape_helper(
                    g,
                    self,
                    g.op("Constant", value_t=torch.tensor([-1], dtype=torch.int64)),
                )
                keepdim = False

            cond_op = g.op(
                "Not",
                g.op("Equal", self, g.op("Constant", value_t=torch.LongTensor([0]))),
            )
            cond_op = g.op(
                "Cast",
                cond_op,
                to_i=_type_utils.JitScalarType.from_value(self).onnx_type(),
            )
            return _reducesum_helper(g, cond_op, axes_i=dim, keepdims_i=keepdim)
    elif ord == 1:
        if g.opset < 18:
            result = _reduce_op_symbolic_helper("ReduceL1")(
                g, self, dim=dim, keepdim=keepdim
            )
        else:
            if axes is None:
                result = _reduce_op_symbolic_helper("ReduceL1")(
                    g, self, keepdim=keepdim
                )
            else:
                result = _reduce_op_symbolic_helper("ReduceL1")(
                    g, self, axes, keepdim=keepdim
                )
    elif ord == 2:
        if g.opset < 18:
            result = _reduce_op_symbolic_helper("ReduceL2")(
                g, self, dim=dim, keepdim=keepdim
            )
        else:
            if axes is None:
                result = _reduce_op_symbolic_helper("ReduceL2")(
                    g, self, keepdim=keepdim
                )
            else:
                result = _reduce_op_symbolic_helper("ReduceL2")(
                    g, self, axes, keepdim=keepdim
                )
    else:
        ord_op = g.op("Constant", value_t=torch.tensor(ord, dtype=torch.float32))
        result = _reducesum_helper(
            g, g.op("Pow", g.op("Abs", self), ord_op), axes_i=dim, keepdims_i=keepdim
        )
        result = g.op(
            "Pow",
            result,
            g.op(
                "Div",
                g.op("Constant", value_t=torch.tensor(1, dtype=torch.float32)),
                ord_op,
            ),
        )

    if not _is_none(dtype):
        dtype = _get_const(dtype, "i", "dtype")
        result = g.op("Cast", result, to_i=_type_utils.JitScalarType(dtype).onnx_type())  # type: ignore[arg-type]
    return result