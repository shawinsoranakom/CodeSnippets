def slice_update(inputs, start_indices, updates):
    inputs = get_ov_output(inputs)
    updates_tensor = get_ov_output(updates)

    if isinstance(start_indices, (list, np.ndarray)):
        start_indices = tuple(start_indices)
    if not isinstance(start_indices, tuple):
        raise ValueError(
            "`slice_update` is not supported by openvino backend"
            " for `start_indices` of type {}".format(type(start_indices))
        )

    zero_scalar = ov_opset.constant(0, Type.i32)
    one_scalar = ov_opset.constant(1, Type.i32)
    zero_tensor = ov_opset.constant([0], Type.i32)
    one_tensor = ov_opset.constant([1], Type.i32)

    processed_start_indices = []
    for idx in start_indices:
        val = get_ov_output(idx)
        if not val.get_element_type().is_integral():
            raise ValueError("`slice_update` requires integral start_indices")
        if val.get_element_type() != Type.i32:
            val = ov_opset.convert(val, Type.i32).output(0)
        if val.get_partial_shape().rank.get_length() == 0:
            val = ov_opset.unsqueeze(val, zero_scalar).output(0)
        processed_start_indices.append(val)

    updates_shape = ov_opset.shape_of(updates_tensor, Type.i32).output(0)
    rank = updates_tensor.get_partial_shape().rank.get_length()
    if rank == 0:
        # Handle scalar update
        start_tensor = ov_opset.concat(processed_start_indices, axis=0).output(
            0
        )
        # For scatter_nd_update,
        # indices should be of shape [num_updates, rank_of_inputs]
        # and updates should be of shape [num_updates]. Here num_updates is 1.
        absolute_indices = ov_opset.unsqueeze(start_tensor, zero_scalar).output(
            0
        )
        updates_flat = ov_opset.unsqueeze(updates_tensor, zero_scalar).output(0)
        result = ov_opset.scatter_nd_update(
            inputs, absolute_indices, updates_flat
        ).output(0)
        return OpenVINOKerasTensor(result)

    # Compute the total number of elements in the updates tensor.
    # Example:
    # if updates.shape = [2, 3], total_elements = 6.
    total_elements = ov_opset.reduce_prod(
        updates_shape, zero_tensor, keep_dims=False
    ).output(0)

    # Generate a flat range [0, 1, ..., total_elements-1].
    # This will be used to enumerate all positions in the updates tensor.
    flat_indices = ov_opset.range(
        zero_scalar, total_elements, one_scalar, output_type=Type.i32
    ).output(0)

    dim_sizes = []
    strides = []

    # For each dimension, compute its size and the stride.
    # (number of elements to skip to move to the next index in this dimension).
    # Example:
    # for shape [2, 3], strides = [3, 1].
    for dim in range(rank):
        dim_size = ov_opset.gather(
            updates_shape, ov_opset.constant([dim], Type.i32), zero_scalar
        ).output(0)
        dim_size_scalar = ov_opset.squeeze(dim_size, zero_tensor).output(0)
        dim_sizes.append(dim_size_scalar)

        # Strides to convert a flat index into a multi-dimensional index.
        # This allows us to map each element in the flattened updates tensor
        # to its correct N-dimensional position, so we can compute the absolute
        # index in the input tensor for the scatter update.
        # Stride for a dimension is the product of all dimensions after it.
        # For the last dimension, stride is 1.
        # Example:
        # For a 3D tensor with shape [2, 3, 4]:
        #   - stride for dim=0 (first axis) is 3*4=12
        #     (to move to the next "block" along axis 0)
        #   - stride for dim=1 is 4 (to move to the next row along axis 1)
        #   - stride for dim=2 is 1 (to move to the next element along axis 2)
        # This is equivalent to how numpy flattens multi-dimensional arrays.
        if dim < rank - 1:
            remaining_dims = ov_opset.slice(
                updates_shape,
                ov_opset.constant([dim + 1], Type.i32),
                ov_opset.constant([rank], Type.i32),
                one_tensor,
                zero_tensor,
            ).output(0)
            stride = ov_opset.reduce_prod(
                remaining_dims, zero_tensor, keep_dims=False
            ).output(0)
        else:
            stride = one_scalar
        strides.append(stride)

    coord_tensors = []
    # For each dimension, compute the coordinate for every flat index.
    # Example:
    # for shape [2, 3], flat index 4 -> coordinates [1, 1] (row 1, col 1).
    for dim in range(rank):
        coords = ov_opset.mod(
            ov_opset.divide(flat_indices, strides[dim]).output(0),
            dim_sizes[dim],
        ).output(0)
        coord_tensors.append(coords)

    coord_tensors_unsqueezed = []
    for coord in coord_tensors:
        # Unsqueeze to make each coordinate a column vector for concatenation.
        coord_unsqueezed = ov_opset.unsqueeze(coord, one_tensor).output(0)
        coord_tensors_unsqueezed.append(coord_unsqueezed)

    # Concatenate all coordinate columns to form [total_elements, rank] matrix.
    # Each row is a multi-dimensional index into the updates tensor.
    # Example:
    # for shape [2, 3], row 4 = [1, 1].
    indices_matrix = ov_opset.concat(coord_tensors_unsqueezed, axis=1).output(0)

    # Broadcast start indices to match the number of updates.
    # Example:
    # start_indices = (2, 3), indices_matrix = [[0,0],[0,1],...],
    # start_broadcast = [[2,3],[2,3],...]
    start_tensor = ov_opset.concat(processed_start_indices, axis=0).output(0)
    start_reshaped = ov_opset.reshape(
        start_tensor, ov_opset.constant([1, rank], Type.i32), special_zero=False
    ).output(0)

    broadcast_shape = ov_opset.concat(
        [
            ov_opset.unsqueeze(total_elements, zero_tensor).output(0),
            one_tensor,
        ],
        axis=0,
    ).output(0)

    start_broadcast = ov_opset.tile(start_reshaped, broadcast_shape).output(0)

    # Add the broadcasted start indices to the relative indices
    # to get absolute indices in the input tensor.
    # Example:
    # if start=(2,3), update index [1,1] -> absolute index [3,4].
    absolute_indices = ov_opset.add(indices_matrix, start_broadcast).output(0)

    # Flatten the updates tensor to match the flat indices.
    updates_flat = ov_opset.reshape(
        updates_tensor,
        ov_opset.unsqueeze(total_elements, zero_tensor).output(0),
        special_zero=False,
    ).output(0)

    # Perform the scatter update: for each absolute index,
    # set the corresponding value from updates_flat.
    result = ov_opset.scatter_nd_update(
        inputs, absolute_indices, updates_flat
    ).output(0)
    return OpenVINOKerasTensor(result)