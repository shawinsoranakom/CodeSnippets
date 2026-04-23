def where(condition, x1=None, x2=None):
    condition = get_ov_output(condition)
    if condition.get_element_type() != Type.boolean:
        condition = ov_opset.convert(condition, Type.boolean).output(0)
    if x1 is None and x2 is None:
        nonzero_indices = ov_opset.non_zero(condition)
        return OpenVINOKerasTensor(nonzero_indices.output(0))
    if x1 is None:
        return OpenVINOKerasTensor(condition)
    if x2 is None:
        raise ValueError("x2 must be provided if x1 is specified.")

    def cast_literal_like_tensor(literal, x):
        ov_type = get_ov_output(x).get_element_type()
        is_bool = ov_type == Type.boolean
        is_float_to_int = isinstance(literal, float) and ov_type.is_integral()
        if is_bool or is_float_to_int:
            return get_ov_output(literal), get_ov_output(x)
        return get_ov_output(literal, ov_type), get_ov_output(x)

    if isinstance(x1, (int, float)):
        x1, x2 = cast_literal_like_tensor(x1, x2)
    elif isinstance(x2, (int, float)):
        x2, x1 = cast_literal_like_tensor(x2, x1)
    else:
        x1 = get_ov_output(x1)
        x2 = get_ov_output(x2)
    x1, x2 = _align_operand_types(x1, x2, "select()")
    return OpenVINOKerasTensor(ov_opset.select(condition, x1, x2).output(0))