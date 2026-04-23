def _var_mean_helper(g: jit_utils.GraphContext, input, dim, correction, keepdim):
    if g.opset < 18:
        if dim is None:
            mean = g.op("ReduceMean", input, keepdims_i=0)
            t_mean = mean
            num_elements = _numel_helper(g, input)
        else:
            mean = g.op("ReduceMean", input, axes_i=dim, keepdims_i=keepdim)
            t_mean = g.op("ReduceMean", input, axes_i=dim, keepdims_i=1)
            redudced_dims = g.op("Shape", input)
            # dim could contain one or multiple dimensions
            redudced_dims = g.op(
                "Gather",
                redudced_dims,
                g.op("Constant", value_t=torch.tensor(dim)),
                axis_i=0,
            )
            num_elements = g.op("ReduceProd", redudced_dims, keepdims_i=0)
        sub_v = g.op("Sub", input, t_mean)
        sqr_sub = g.op("Mul", sub_v, sub_v)
        keepdim_mean = 0 if dim is None else keepdim
        var = g.op("ReduceMean", sqr_sub, axes_i=dim, keepdims_i=keepdim_mean)
        # Correct bias in calculating variance, by dividing it over (N - correction) instead on N
        if correction is None:
            correction = 1
        if correction != 0:
            num_elements = g.op(
                "Cast", num_elements, to_i=_C_onnx.TensorProtoDataType.FLOAT
            )
            one = g.op("Constant", value_t=torch.tensor(correction, dtype=torch.float))
            mul = g.op("Mul", var, num_elements)
            var = g.op("Div", mul, g.op("Sub", num_elements, one))
        return var, mean
    else:
        axes = None
        if dim is None:
            mean = g.op("ReduceMean", input, keepdims_i=0)
            t_mean = mean
            num_elements = _numel_helper(g, input)
        else:
            axes = g.op("Constant", value_t=torch.tensor(dim, dtype=torch.long))
            mean = g.op("ReduceMean", input, axes, keepdims_i=keepdim)
            t_mean = g.op("ReduceMean", input, axes, keepdims_i=1)
            redudced_dims = g.op("Shape", input)
            # dim could contain one or multiple dimensions
            redudced_dims = g.op(
                "Gather",
                redudced_dims,
                g.op("Constant", value_t=torch.tensor(dim)),
                axis_i=0,
            )
            num_elements = g.op("ReduceProd", redudced_dims, keepdims_i=0)
        sub_v = g.op("Sub", input, t_mean)
        sqr_sub = g.op("Mul", sub_v, sub_v)
        keepdim_mean = 0 if dim is None else keepdim
        if axes is None:
            var = g.op("ReduceMean", sqr_sub, keepdims_i=keepdim_mean)
        else:
            var = g.op("ReduceMean", sqr_sub, axes, keepdims_i=keepdim_mean)
        # Correct bias in calculating variance, by dividing it over (N - correction) instead on N
        if correction is None:
            correction = 1
        if correction != 0:
            num_elements = g.op(
                "Cast", num_elements, to_i=_C_onnx.TensorProtoDataType.FLOAT
            )
            one = g.op("Constant", value_t=torch.tensor(correction, dtype=torch.float))
            mul = g.op("Mul", var, num_elements)
            var = g.op("Div", mul, g.op("Sub", num_elements, one))
        return var, mean