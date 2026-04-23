def shape_to_ov_output(shape):
    """Convert a shape tuple/list to an i32 ov.Output.

    Unlike get_ov_output, handles mixed shapes where some dims are
    OpenVINOKerasTensor scalars (from ops.shape() on dynamic tensors).
    """
    if not isinstance(shape, (list, tuple)):
        raise ValueError(f"shape must be a list or tuple, got {type(shape)}")
    if not any(isinstance(e, (OpenVINOKerasTensor, ov.Output)) for e in shape):
        return ov_opset.constant(list(shape), Type.i32).output(0)
    parts = []
    for e in shape:
        if isinstance(e, OpenVINOKerasTensor):
            elem = e.output
        elif isinstance(e, ov.Output):
            elem = e
        else:
            elem = ov_opset.constant([e], Type.i32).output(0)
        if elem.get_element_type() != Type.i32:
            elem = ov_opset.convert(elem, Type.i32).output(0)
        # Scalar dims need to be reshaped to [1] for concat
        ps = elem.get_partial_shape()
        if ps.rank.is_static and ps.rank.get_length() == 0:
            elem = ov_opset.reshape(
                elem, ov_opset.constant([1], Type.i32).output(0), False
            ).output(0)
        parts.append(elem)
    return ov_opset.concat(parts, 0).output(0)