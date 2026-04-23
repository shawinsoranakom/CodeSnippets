def map_coordinates(
    inputs, coordinates, order, fill_mode="constant", fill_value=0.0
):
    input_arr = convert_to_tensor(inputs)
    coordinate_arrs = convert_to_tensor(coordinates)

    if coordinate_arrs.shape[0] != len(input_arr.shape):
        raise ValueError(
            "First dim of `coordinates` must be the same as the rank of "
            "`inputs`. "
            f"Received inputs with shape: {input_arr.shape} and coordinate "
            f"leading dim of {coordinate_arrs.shape[0]}"
        )
    if len(coordinate_arrs.shape) < 2:
        raise ValueError(
            "Invalid coordinates rank: expected at least rank 2."
            f" Received input with shape: {coordinate_arrs.shape}"
        )
    if fill_mode not in MAP_COORDINATES_FILL_MODES:
        raise ValueError(
            "Invalid value for argument `fill_mode`. Expected one of "
            f"{set(MAP_COORDINATES_FILL_MODES.keys())}. Received: "
            f"fill_mode={fill_mode}"
        )

    fill_value = convert_to_tensor(fill_value, dtype=input_arr.dtype)

    coordinate_arrs = tf.unstack(coordinate_arrs, axis=0)

    if order == 0:
        interp_fun = _nearest_indices_and_weights
    elif order == 1:
        interp_fun = _linear_indices_and_weights
    else:
        raise NotImplementedError("map_coordinates currently requires order<=1")

    def process_coordinates(coords, size):
        if fill_mode == "constant":
            valid = (coords >= 0) & (coords < size)
            safe_coords = tf.clip_by_value(coords, 0, size - 1)
            return safe_coords, valid
        elif fill_mode == "nearest":
            return tf.clip_by_value(coords, 0, size - 1), tf.ones_like(
                coords, dtype=tf.bool
            )
        elif fill_mode in ["mirror", "reflect"]:
            coords = tf.abs(coords)
            size_2 = size * 2
            mod = tf.math.mod(coords, size_2)
            under = mod < size
            over = ~under
            # reflect mode is same as mirror for under
            coords = tf.where(under, mod, size_2 - mod)
            # for reflect mode, adjust the over case
            if fill_mode == "reflect":
                coords = tf.where(over, coords - 1, coords)
            return coords, tf.ones_like(coords, dtype=tf.bool)
        elif fill_mode == "wrap":
            coords = tf.math.mod(coords, size)
            return coords, tf.ones_like(coords, dtype=tf.bool)
        else:
            raise ValueError(f"Unknown fill_mode: {fill_mode}")

    valid_1d_interpolations = []
    for coordinate, size in zip(coordinate_arrs, input_arr.shape):
        interp_nodes = interp_fun(coordinate)
        valid_interp = []
        for index, weight in interp_nodes:
            safe_index, valid = process_coordinates(index, size)
            valid_interp.append((safe_index, valid, weight))
        valid_1d_interpolations.append(valid_interp)

    outputs = []
    for items in itertools.product(*valid_1d_interpolations):
        indices, validities, weights = zip(*items)
        indices = tf.transpose(tf.stack(indices))

        gathered = tf.transpose(tf.gather_nd(input_arr, indices))

        # Cast to computation dtype early to avoid type issues
        dtype = weights[0].dtype
        gathered = tf.cast(gathered, dtype)
        gathered = tf.cast(gathered, weights[0].dtype)

        if fill_mode == "constant":
            all_valid = tf.reduce_all(validities, axis=0)
            fill_value_typed = tf.cast(fill_value, dtype)
            gathered = tf.where(all_valid, gathered, fill_value_typed)

        outputs.append(functools.reduce(operator.mul, weights) * gathered)

    result = functools.reduce(operator.add, outputs)

    if input_arr.dtype.is_integer:
        result = tf.round(result)
    return tf.cast(result, input_arr.dtype)