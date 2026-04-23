def map_coordinates(
    inputs, coordinates, order, fill_mode="constant", fill_value=0
):
    fill_modes = {"constant", "nearest", "wrap", "mirror", "reflect"}
    if fill_mode not in fill_modes:
        raise ValueError(
            "Invalid value for argument `fill_mode`. Expected one of "
            f"{fill_modes}. Received: fill_mode={fill_mode}"
        )
    if order not in (0, 1):
        raise ValueError(
            "Invalid value for argument `order`. Expected one of "
            f"[0, 1]. Received: order={order}"
        )

    inputs = convert_to_tensor(inputs)
    coordinates = convert_to_tensor(coordinates)
    inputs_ov = get_ov_output(inputs)
    coords_ov = get_ov_output(coordinates)
    input_shape = inputs_ov.get_partial_shape()
    ndim = input_shape.rank.get_length()
    coords_shape = coords_ov.get_partial_shape()
    if coords_shape.rank.is_static and coords_shape.rank.get_length() < 2:
        raise ValueError(
            "Invalid coordinates rank: expected at least rank 2."
            f" Received input with shape: {tuple(coords_shape.to_shape())}"
        )
    if coords_shape[0].is_static and coords_shape[0].get_length() != ndim:
        raise ValueError(
            "First dim of `coordinates` must be the same as the rank of "
            "`inputs`. "
            f"Received inputs with shape: {tuple(input_shape.to_shape())} and "
            f"coordinate leading dim of {coords_shape[0].get_length()}"
        )
    ov_type = inputs_ov.get_element_type()

    # Coordinates must be float for arithmetic
    coords_ov = ov_opset.convert(coords_ov, Type.f32).output(0)

    # Split coordinates into per-dimension tensors, each shape [*output_shape]
    axis_0 = ov_opset.constant(0, dtype=Type.i32).output(0)
    coord_list = [
        ov_opset.gather(
            coords_ov,
            ov_opset.constant(i, dtype=Type.i32).output(0),
            axis_0,
        ).output(0)
        for i in range(ndim)
    ]

    input_shape_node = ov_opset.shape_of(
        inputs_ov, output_type=Type.i32
    ).output(0)
    size_nodes = [
        ov_opset.gather(
            input_shape_node,
            ov_opset.constant(i, dtype=Type.i32).output(0),
            axis_0,
        ).output(0)
        for i in range(ndim)
    ]

    def fix_index(index, size_node):
        if fill_mode in ("constant", "nearest"):
            zero = ov_opset.constant(0, dtype=Type.i32).output(0)
            size_m1 = ov_opset.subtract(
                size_node, ov_opset.constant(1, dtype=Type.i32)
            ).output(0)
            return ov_opset.minimum(
                ov_opset.maximum(index, zero), size_m1
            ).output(0)
        elif fill_mode == "wrap":
            return ov_opset.floor_mod(index, size_node).output(0)
        elif fill_mode == "mirror":
            return _mirror_index_fixer(index, size_node)
        else:  # reflect
            return _reflect_index_fixer(index, size_node)

    def is_valid(index, size_node):
        if fill_mode != "constant":
            return None
        return ov_opset.logical_and(
            ov_opset.greater_equal(index, ov_opset.constant(0, dtype=Type.i32)),
            ov_opset.less(index, size_node),
        ).output(0)

    # Build per-dimension interpolation nodes
    interp_nodes_per_dim = []
    for i, coord in enumerate(coord_list):
        size_node = size_nodes[i]
        if order == 0:
            idx = ov_opset.convert(
                ov_opset.round(coord, mode="half_to_even"), Type.i32
            ).output(0)
            interp_nodes_per_dim.append(
                [(fix_index(idx, size_node), is_valid(idx, size_node), None)]
            )
        else:
            lower_f = ov_opset.floor(coord).output(0)
            upper_w = ov_opset.subtract(coord, lower_f).output(0)
            lower_w = ov_opset.subtract(
                ov_opset.constant(1.0, dtype=Type.f32), upper_w
            ).output(0)
            lower_idx = ov_opset.convert(lower_f, Type.i32).output(0)
            upper_idx = ov_opset.add(
                lower_idx, ov_opset.constant(1, dtype=Type.i32)
            ).output(0)
            interp_nodes_per_dim.append(
                [
                    (
                        fix_index(lower_idx, size_node),
                        is_valid(lower_idx, size_node),
                        lower_w,
                    ),
                    (
                        fix_index(upper_idx, size_node),
                        is_valid(upper_idx, size_node),
                        upper_w,
                    ),
                ]
            )

    fill_const = ov_opset.convert(
        ov_opset.constant(float(fill_value), dtype=Type.f32), ov_type
    ).output(0)

    output = None
    for items in itertools.product(*interp_nodes_per_dim):
        indices, validities, weights = zip(*items)

        # Stack indices: [*output_shape, ndim] for gather_nd
        stacked = ov_opset.concat(
            [ov_opset.unsqueeze(idx, axes=[-1]).output(0) for idx in indices],
            axis=-1,
        ).output(0)
        gathered = ov_opset.gather_nd(inputs_ov, stacked).output(0)

        if fill_mode == "constant":
            valid = validities[0]
            for v in validities[1:]:
                valid = ov_opset.logical_and(valid, v).output(0)
            gathered = ov_opset.select(valid, gathered, fill_const).output(0)

        if any(w is not None for w in weights):
            result_type = ov_type if not ov_type.is_integral() else Type.f32
            contribution = ov_opset.convert(gathered, result_type).output(0)
            for w in weights:
                if w is not None:
                    contribution = ov_opset.multiply(
                        contribution,
                        ov_opset.convert(w, result_type).output(0),
                    ).output(0)
        else:
            contribution = gathered

        output = (
            contribution
            if output is None
            else ov_opset.add(output, contribution).output(0)
        )

    if ov_type.is_integral() and order == 1:
        output = ov_opset.convert(
            ov_opset.round(
                ov_opset.convert(output, Type.f32).output(0),
                mode="half_to_even",
            ).output(0),
            ov_type,
        ).output(0)

    return OpenVINOKerasTensor(output)