def _write_sub_tensor_to_file_optimized(
    full_tensor_mv: memoryview,
    sub_tensor_bytes: bytes,
    element_size: int,
    tensor_shape: list[int],
    sub_tensor_offsets: list[int],
    sub_tensor_shape: list[int],
) -> None:
    """
    Optimized version that writes the maximum number of contiguous bytes possible.

    Uses a unified algorithm that calculates the maximum contiguous bytes that can be
    written in each iteration and continues until the entire subtensor is written.
    Handles all sharding patterns efficiently:
    - Full sub-tensor at once for row-wise sharding
    - Row-by-row for column-wise sharding
    - Optimized chunks for other patterns

    Args:
        full_tensor_mv: Buffer to write the full tensor to
        sub_tensor_bytes: Raw tensor data as bytes
        element_size: Size of each element in bytes
        tensor_shape: Shape of the full tensor
        sub_tensor_offsets: Starting offsets of the sub-tensor within the full tensor
        sub_tensor_shape: Shape of the sub-tensor
    """
    # Handle empty tensors
    if not tensor_shape or not sub_tensor_shape:
        return

    # Calculate tensor strides for efficient indexing
    tensor_strides = [1]
    for i in range(len(tensor_shape) - 1, 0, -1):
        tensor_strides.insert(0, tensor_strides[0] * tensor_shape[i])

    sub_tensor_strides = [1]
    for i in range(len(sub_tensor_shape) - 1, 0, -1):
        sub_tensor_strides.insert(0, sub_tensor_strides[0] * sub_tensor_shape[i])

    total_elements = math.prod(sub_tensor_shape)

    elements_written = 0
    while elements_written < total_elements:
        # Convert linear index to multi-dimensional indices
        temp_idx = elements_written
        indices = []
        for dim_size in reversed(sub_tensor_shape):
            indices.append(temp_idx % dim_size)
            temp_idx //= dim_size
        indices.reverse()

        # Calculate maximum contiguous elements we can write from this position
        max_contiguous = _calculate_max_contiguous_elements(
            indices, sub_tensor_shape, tensor_shape
        )

        # Calculate source position in bytes
        src_pos = sum(idx * stride for idx, stride in zip(indices, sub_tensor_strides))
        src_byte_offset = src_pos * element_size

        # Calculate destination position in bytes
        dest_indices = [
            idx + offset for idx, offset in zip(indices, sub_tensor_offsets)
        ]
        dest_pos = sum(
            idx * stride for idx, stride in zip(dest_indices, tensor_strides)
        )
        dest_byte_offset = dest_pos * element_size

        # Write the contiguous chunk
        bytes_to_write = max_contiguous * element_size
        chunk_data = sub_tensor_bytes[
            src_byte_offset : src_byte_offset + bytes_to_write
        ]
        full_tensor_mv[dest_byte_offset : dest_byte_offset + bytes_to_write] = (
            chunk_data
        )

        elements_written += max_contiguous