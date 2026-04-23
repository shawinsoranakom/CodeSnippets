def reshape(x, newshape):
    x = get_ov_output(x)
    if isinstance(newshape, int):
        newshape = [newshape]
    elif isinstance(newshape, tuple):
        newshape = list(newshape)
    if isinstance(newshape, list):
        has_dyn = False
        for _d in newshape:
            if isinstance(_d, OpenVINOKerasTensor):
                has_dyn = True
                break
        if has_dyn:
            # Build a shape tensor from mixed static/dynamic dims
            axis = ov_opset.constant(0, Type.i32).output(0)
            dim_tensors = []
            for d in newshape:
                if isinstance(d, OpenVINOKerasTensor):
                    d_ov = get_ov_output(d)
                    rank = d_ov.get_partial_shape().rank
                    if rank.is_static and rank.get_length() == 0:
                        d_ov = ov_opset.unsqueeze(d_ov, axis).output(0)
                    dim_tensors.append(d_ov)
                else:
                    val = -1 if d is None else d
                    dim_tensors.append(
                        ov_opset.constant([val], Type.i32).output(0)
                    )
            newshape = ov_opset.concat(dim_tensors, 0).output(0)
            return OpenVINOKerasTensor(
                ov_opset.reshape(x, newshape, False).output(0)
            )
        newshape = [-1 if d is None else d for d in newshape]
    if isinstance(newshape, OpenVINOKerasTensor):
        newshape = get_ov_output(newshape)
    else:
        newshape = ov_opset.constant(newshape, Type.i32).output(0)
    return OpenVINOKerasTensor(ov_opset.reshape(x, newshape, False).output(0))