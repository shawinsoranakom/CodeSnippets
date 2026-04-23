def meshgrid(*x, indexing="xy"):
    if len(x) < 2:
        raise ValueError(
            "meshgrid requires at least 2 input arrays. "
            f"Received: {len(x)} input array(s)."
        )
    if indexing not in ("xy", "ij"):
        raise ValueError("indexing must be either 'xy' or 'ij'")

    tensors = [get_ov_output(xi) for xi in x]
    n = len(tensors)

    shapes = [
        ov_opset.shape_of(t, Type.i64).output(0) for t in tensors
    ]  # each is [Ni]
    one = ov_opset.constant([1], Type.i64).output(0)

    if indexing == "xy":
        shape_list = [shapes[1], shapes[0]] + shapes[2:]
        out_shape = ov_opset.concat(shape_list, axis=0).output(0)
    else:
        out_shape = ov_opset.concat(shapes, axis=0).output(0)

    outputs = []
    for i, t in enumerate(tensors):
        reshape_parts = [one] * n
        if indexing == "xy":
            if i == 0:
                reshape_parts[1] = shapes[0]
            elif i == 1:
                reshape_parts[0] = shapes[1]
            else:
                reshape_parts[i] = shapes[i]
        else:
            reshape_parts[i] = shapes[i]

        reshape_shape = ov_opset.concat(reshape_parts, axis=0).output(0)
        reshaped = ov_opset.reshape(t, reshape_shape, False).output(0)
        broadcasted = ov_opset.broadcast(reshaped, out_shape).output(0)
        outputs.append(OpenVINOKerasTensor(broadcasted))

    return outputs