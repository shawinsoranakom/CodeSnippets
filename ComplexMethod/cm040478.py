def concatenate(xs, axis=0):
    elems = [get_ov_output(x) for x in xs]
    if axis is None:
        flatten_shape = ov_opset.constant([-1], Type.i32).output(0)
        elems = [
            ov_opset.reshape(x, flatten_shape, False).output(0) for x in elems
        ]
        axis = 0
    keras_types = [ov_to_keras_type(x.get_element_type()) for x in elems]
    if keras_types:
        target_type = dtypes.result_type(*keras_types)
        ov_target_type = OPENVINO_DTYPES[target_type]
        elems = [
            ov_opset.convert(x, ov_target_type).output(0)
            if x.get_element_type() != ov_target_type
            else x
            for x in elems
        ]
    res = ov_opset.concat(elems, axis).output(0)
    return OpenVINOKerasTensor(res)