def slice(g: jit_utils.GraphContext, self, *args):
    if len(args) == 4:
        # aten::slice(Tensor self, int dim, int start, int end, int step) -> Tensor
        dim, start, end, step = args
        step = symbolic_helper._parse_arg(step, "i")
        if step != 1:
            raise errors.SymbolicValueError("step!=1 is currently not supported", self)
        is_start_none = start.node().kind() == "prim::Constant" and isinstance(
            start.type(), _C.NoneType
        )
        is_end_none = end.node().kind() == "prim::Constant" and isinstance(
            end.type(), _C.NoneType
        )
        is_start_onnx_const = start.node().kind() == "onnx::Constant"
        is_end_onnx_const = end.node().kind() == "onnx::Constant"
        if (
            ((not is_start_none) and (not is_start_onnx_const))
            or ((not is_end_none) and (not is_end_onnx_const))
            or dim.node().kind() != "onnx::Constant"
        ):
            if GLOBALS.operator_export_type == _C_onnx.OperatorExportTypes.ONNX:
                raise errors.SymbolicValueError(
                    "Unsupported: ONNX export of Slice with dynamic inputs. DynamicSlice "
                    "is a deprecated experimental op. Please use statically allocated "
                    "variables or export to a higher opset version.",
                    self,
                )
            else:
                start_unsqueezed = symbolic_helper._unsqueeze_helper(g, start, [0])
                end_unsqueezed = symbolic_helper._unsqueeze_helper(g, end, [0])
                dim_unsqueezed = symbolic_helper._unsqueeze_helper(g, dim, [0])
                return g.op(
                    "DynamicSlice",
                    self,
                    start_unsqueezed,
                    end_unsqueezed,
                    dim_unsqueezed,
                )
        else:
            start = 0 if is_start_none else symbolic_helper._parse_arg(start, "i")
            end = (
                _constants.INT64_MAX
                if is_end_none
                else symbolic_helper._parse_arg(end, "i")
            )
            dim = symbolic_helper._parse_arg(dim, "i")
            return symbolic_helper._slice_helper(
                g, self, axes=[dim], starts=[start], ends=[end]
            )
    elif len(args) == 3:
        # aten::slice(t[] l, int start, int end, int step) -> t[]
        start, end, step = args
        dim = 0
        is_start_none = start.node().kind() == "prim::Constant" and isinstance(
            start.type(), _C.NoneType
        )
        is_end_none = end.node().kind() == "prim::Constant" and isinstance(
            end.type(), _C.NoneType
        )
        start = 0 if is_start_none else symbolic_helper._parse_arg(start, "i")
        end = (
            _constants.INT64_MAX
            if is_end_none
            else symbolic_helper._parse_arg(end, "i")
        )
        return symbolic_helper._slice_helper(
            g, self, axes=[dim], starts=[start], ends=[end]
        )

    return symbolic_helper._unimplemented("aten::slice", f"with {len(args)} arguments")