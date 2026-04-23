def get_packed_weights(param, empty_param, device_mesh, rank, dim):
    """
    When weights are packed (gate_up_proj), we need to make sure each shard gets its correct share.
    So if you have: gate_proj       ( 16, 5120, 8190)
    and             up_proj         ( 16, 5120, 8190)
    packed as       gate_up_proj    ( 16, 5120, 2 * 8190)
    And you shard along the last dimension, you need to interleave the gate and up values:

    Now, if we shard along the last dimension across TP_size (Tensor Parallelism size), we must interleave the values from gate and up projections correctly.

    Let's take TP_size = 4 for an example:

    Packed tensor `gate_up_proj`
    ---------------------------------------------------------------
    [ G0  G1  G2  G3 | G4  G5  G6  G7 | ... | U0  U1  U2  U3 | U4  U5  U6  U7 | ... ]
     ↑─────────────↑   ↑─────────────↑        ↑─────────────↑  ↑─────────────↑
       Gate Slice 0      Gate Slice 1            Up Slice 0       Up Slice 1

    Explanation:
    - The first half of the tensor (left of the center) holds the gate_proj values.
    - The second half (right of the center) holds the up_proj values.
    - For TP=4, we divide each half into 4 slices. In this example, we show two slices for brevity.
    - Each shard receives one slice from the gate part and the corresponding slice from the up part.

    For instance:
    • Shard 0 gets: [ Gate Slice 0, Up Slice 0 ] = [ G0, G1, G2, G3, U0, U1, U2, U3 ]
    • Shard 1 gets: [ Gate Slice 1, Up Slice 1 ] = [ G4, G5, G6, G7, U4, U5, U6, U7 ]
    • … and so on.

    This ensures that each shard receives an equal portion of both gate and up projections, maintaining consistency across tensor parallelism.
    """
    slice_ = param
    total_size = empty_param.shape[dim]
    world_size = device_mesh.size()
    block_sizes = _blocks_to_block_sizes(total_size=total_size, blocks=2)

    tensors_slices = []
    block_offset = 0
    for block_size in block_sizes:
        shard_block_size = block_size // world_size
        start = rank * shard_block_size
        stop = (rank + 1) * shard_block_size
        tensors_slices += range(block_offset + start, block_offset + stop)
        block_offset += block_size

    slice_dtype = slice_.get_dtype()
    # Handle F8_E4M3 dtype by converting to float16 before slicing
    # Without upcasting, the slicing causes : RuntimeError: "index_cpu" not implemented for 'Float8_e4m3fn'
    casted = False
    if slice_dtype == "F8_E4M3" or slice_dtype == "F8_E5M2":
        slice_ = slice_[...].to(torch.float16)
        casted = True

    if dim == 0:
        tensor = slice_[tensors_slices, ...]
    elif dim == 1 or dim == -2:
        tensor = slice_[:, tensors_slices, ...]
    elif dim == 2 or dim == -1:
        tensor = slice_[..., tensors_slices]
    else:
        raise ValueError(f"Unsupported dim {dim}, only dim 0, 1 or 2 are supported")

    if casted:
        return tensor
    else:
        return tensor.to(str_to_dtype[slice_dtype])