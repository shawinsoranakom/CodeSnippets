def randint(shape, minval, maxval, dtype="int32", seed=None):
    dtype = dtype or "int32"
    ov_dtype = OPENVINO_DTYPES[dtype]
    seed_val = draw_seed(seed)
    if isinstance(seed_val, OpenVINOKerasTensor):
        seed1, seed2 = convert_to_numpy(seed_val)
    else:
        seed1, seed2 = seed_val.data
    if ov_dtype in (Type.i64, Type.u64, Type.u32):
        gen_dtype = Type.i64
    else:
        gen_dtype = Type.i32
    if isinstance(shape, (list, tuple)):
        shape = ov_opset.constant(list(shape), Type.i32).output(0)
    elif isinstance(shape, OpenVINOKerasTensor):
        shape = shape.output
    elif isinstance(shape, int):
        shape = ov_opset.constant([shape], Type.i32).output(0)
    else:
        shape = get_ov_output(shape, Type.i32)
    minval = get_ov_output(minval, gen_dtype)
    maxval = get_ov_output(maxval, gen_dtype)
    if minval.get_element_type() != gen_dtype:
        minval = ov_opset.convert(minval, gen_dtype).output(0)
    if maxval.get_element_type() != gen_dtype:
        maxval = ov_opset.convert(maxval, gen_dtype).output(0)
    rand = _random_uniform(shape, minval, maxval, gen_dtype, seed1, seed2)
    if ov_dtype != gen_dtype:
        result = ov_opset.convert(rand, ov_dtype).output(0)
    else:
        result = rand
    return OpenVINOKerasTensor(result)