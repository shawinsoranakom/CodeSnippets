def symbolic(g, self, dim=None, keepdim=None):
        self = _maybe_cast_reduce_op_input(g, self)
        if dim is None or dim == ():
            # Dim can be 0, which will cause (not dim) == True. So we don't want to do
            # (not dim)
            # all-reduce path
            return _handle_reduce_dim_none(g, self, onnx_op_name)
        else:
            # dim-reduce path
            keepdim = _get_const(keepdim, "i", "keepdim")
            if g.opset < 18:
                desc = "is" if allow_multi_dim_support else "i"
                dim = _get_const(dim, desc, "dim")
                dim_list = dim if allow_multi_dim_support else [dim]
                return g.op(onnx_op_name, self, axes_i=dim_list, keepdims_i=keepdim)
            else:
                if _is_value(dim):
                    axes = dim
                else:
                    if allow_multi_dim_support:
                        axes = g.op(
                            "Constant", value_t=torch.tensor(dim, dtype=torch.long)
                        )
                    else:
                        axes = g.op(
                            "Constant", value_t=torch.tensor([dim], dtype=torch.long)
                        )
                return g.op(onnx_op_name, self, axes, keepdims_i=keepdim)