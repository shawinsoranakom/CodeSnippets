def while_loop(
    cond,
    body,
    loop_vars,
    maximum_iterations=None,
):
    def flatten_structure(data):
        if isinstance(data, dict):
            return [v for k in sorted(data) for v in flatten_structure(data[k])]
        elif isinstance(data, (tuple, list)):
            return [v for item in data for v in flatten_structure(item)]
        else:
            return [data]

    def pack_structure(template, flat):
        if isinstance(template, dict):
            keys = sorted(template)
            packed = {}
            for k in keys:
                value, flat = pack_structure(template[k], flat)
                packed[k] = value
            return packed, flat
        elif isinstance(template, (tuple, list)):
            packed = []
            for item in template:
                value, flat = pack_structure(item, flat)
                packed.append(value)
            return (
                tuple(packed) if isinstance(template, tuple) else packed
            ), flat
        else:
            return flat[0], flat[1:]

    is_scalar_input = _is_scalar(loop_vars)

    if is_scalar_input:
        loop_vars = (loop_vars,)
    elif isinstance(loop_vars, (list, np.ndarray)):
        loop_vars = tuple(loop_vars)
    else:
        if not isinstance(loop_vars, (tuple, dict)):
            raise ValueError(
                "Expected tuple or dict for `loop_vars`, "
                f"Received: {type(loop_vars)}"
            )

    flat_loop_vars = flatten_structure(loop_vars)
    loop_vars_ov = [get_ov_output(var) for var in flat_loop_vars]

    maximum_iterations = (
        ov_opset.constant(-1, Type.i32).output(0)
        if maximum_iterations is None
        else get_ov_output(maximum_iterations)
    )

    trip_count = maximum_iterations
    execution_condition = ov_opset.constant(True, Type.boolean).output(0)
    loop = ov_opset.loop(trip_count, execution_condition)

    shapes = [var.get_partial_shape() for var in loop_vars_ov]
    types = [var.get_element_type() for var in loop_vars_ov]
    params = [
        ov_opset.parameter(shape, dtype) for shape, dtype in zip(shapes, types)
    ]
    param_tensors = [OpenVINOKerasTensor(p.output(0)) for p in params]

    packed_args, _ = pack_structure(loop_vars, param_tensors)
    if isinstance(packed_args, dict):
        body_out = body(packed_args)
    else:
        body_out = body(*packed_args)

    if not isinstance(body_out, (list, tuple, dict)):
        body_out = (body_out,)

    flat_body_out = flatten_structure(body_out)
    if isinstance(packed_args, dict):
        cond_output = get_ov_output(cond(body_out))
    else:
        cond_output = get_ov_output(cond(*body_out))

    if len(cond_output.get_partial_shape()) != 0:
        raise ValueError(
            "`cond` function must return a scalar boolean value, "
            "but got shape {}".format(cond_output.get_partial_shape())
        )

    for p, out in zip(params, flat_body_out):
        out_shape = get_ov_output(out).get_partial_shape()
        p.set_partial_shape(out_shape)

    results = [cond_output] + [get_ov_output(x) for x in flat_body_out]
    body_func = Model(results=results, parameters=params)
    loop.set_function(body_func)
    loop.set_special_body_ports([-1, 0])

    for param, init_val, next_val in zip(params, loop_vars_ov, flat_body_out):
        loop.set_merged_input(param, init_val, get_ov_output(next_val))

    outputs_flat = [
        OpenVINOKerasTensor(loop.get_iter_value(get_ov_output(val)))
        for val in flat_body_out
    ]
    final_output, _ = pack_structure(loop_vars, outputs_flat)

    if is_scalar_input:
        if isinstance(final_output, tuple):
            return final_output[0]
        else:
            return final_output
    else:
        return final_output