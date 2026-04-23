def dropout(inputs, rate, noise_shape=None, seed=None):
    inputs_ov = get_ov_output(inputs)
    dtype = inputs_ov.get_element_type()

    seed_val = draw_seed(seed)
    if isinstance(seed_val, OpenVINOKerasTensor):
        seed1, seed2 = convert_to_numpy(seed_val)
    else:
        seed1, seed2 = seed_val.data

    if not isinstance(rate, (int, float)):
        rate = get_ov_output(rate, dtype)
    else:
        rate = ov_opset.constant(rate, dtype).output(0)

    one = ov_opset.constant(1.0, dtype).output(0)
    keep_prob = ov_opset.subtract(one, rate).output(0)

    if noise_shape is None:
        noise_shape_node = ov_opset.shape_of(inputs_ov, Type.i32).output(0)
    else:
        shape_elements = []
        input_shape_node = ov_opset.shape_of(inputs_ov, Type.i32).output(0)
        zero_index = ov_opset.constant(0, Type.i32).output(0)

        for i, dim in enumerate(noise_shape):
            if dim is None:
                indices = ov_opset.constant([i], Type.i32).output(0)
                dim_node = ov_opset.gather(
                    input_shape_node, indices, zero_index
                ).output(0)
                shape_elements.append(dim_node)
            else:
                shape_elements.append(
                    ov_opset.constant([dim], Type.i32).output(0)
                )

        noise_shape_node = ov_opset.concat(shape_elements, 0).output(0)

    gen_dtype = dtype
    if dtype in (Type.bf16, Type.f16):
        gen_dtype = Type.f32

    min_val = ov_opset.constant(0.0, gen_dtype).output(0)
    max_val = ov_opset.constant(1.0, gen_dtype).output(0)

    rand = _random_uniform(
        noise_shape_node, min_val, max_val, gen_dtype, seed1, seed2
    )

    if gen_dtype != dtype:
        keep_prob_gen = ov_opset.convert(keep_prob, gen_dtype).output(0)
        mask = ov_opset.less(rand, keep_prob_gen).output(0)
    else:
        mask = ov_opset.less(rand, keep_prob).output(0)

    zero = ov_opset.constant(0.0, dtype).output(0)
    one_dtype = ov_opset.constant(1.0, dtype).output(0)

    is_zero_prob = ov_opset.equal(keep_prob, zero).output(0)
    safe_prob = ov_opset.select(is_zero_prob, one_dtype, keep_prob).output(0)
    inv_prob = ov_opset.divide(one_dtype, safe_prob).output(0)
    scale = ov_opset.select(is_zero_prob, zero, inv_prob).output(0)

    mask_casted = ov_opset.convert(mask, dtype).output(0)

    masked_inputs = ov_opset.multiply(inputs_ov, mask_casted).output(0)
    result = ov_opset.multiply(masked_inputs, scale).output(0)

    return OpenVINOKerasTensor(result)