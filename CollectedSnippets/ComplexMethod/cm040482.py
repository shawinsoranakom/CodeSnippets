def dstack(xs):
    if not isinstance(xs, (list, tuple)):
        xs = (xs,)
    elems = [convert_to_tensor(elem) for elem in xs]
    element_type = elems[0].output.get_element_type()
    elems = [get_ov_output(elem, element_type) for elem in elems]

    processed_elems = []
    for elem in elems:
        shape = elem.get_partial_shape()
        rank = shape.rank
        shape_len = rank.get_length()
        if shape_len == 0:
            elem = ov_opset.unsqueeze(
                elem, ov_opset.constant(0, Type.i32)
            ).output(0)
            elem = ov_opset.unsqueeze(
                elem, ov_opset.constant(1, Type.i32)
            ).output(0)
            elem = ov_opset.unsqueeze(
                elem, ov_opset.constant(2, Type.i32)
            ).output(0)
        elif shape_len == 1:
            elem = ov_opset.unsqueeze(
                elem, ov_opset.constant(0, Type.i32)
            ).output(0)
            elem = ov_opset.unsqueeze(
                elem, ov_opset.constant(2, Type.i32)
            ).output(0)
        elif shape_len == 2:
            elem = ov_opset.unsqueeze(
                elem, ov_opset.constant(2, Type.i32)
            ).output(0)
        processed_elems.append(elem)

    for i in range(1, len(processed_elems)):
        processed_elems[0], processed_elems[i] = _align_operand_types(
            processed_elems[0], processed_elems[i], "dstack()"
        )
    return OpenVINOKerasTensor(ov_opset.concat(processed_elems, 2).output(0))