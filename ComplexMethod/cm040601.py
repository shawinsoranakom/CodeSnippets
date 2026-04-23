def gptq_quantize_matrix(
    weights_transpose,
    inv_hessian,
    *,
    blocksize=128,
    group_size=-1,
    activation_order=False,
    order_metric=None,
    compute_scale_zero=compute_quantization_parameters,
):
    """
    Implements the GPTQ error correction updates.

    For a single column update (column j):
        e = invH[j, j] * (w_j - q_j)
        W[:, j+1:] -= e * invH[j, j+1:]
    where:
    - w_j is the original column,
    - q_j is the quantized column,
    - invH is the inverse Hessian,
    - e is the propagated error term.

    Across entire blocks:
        W[:, future] -= E_block * invH[block, future]
    where:
    - E_block is the quantization error accumulated for the current block,
    - invH[block, future] denotes the cross-block slice of the inverse Hessian,
    - W[:, future] are the columns yet to be quantized.

    Args:
        weights_transpose: Transposed weight matrix [out_features, in_features]
         to quantize.
        inv_hessian: Inverse Hessian matrix [in_features, in_features] for
         error propagation.
        blocksize: Size of the blocks to process (default: 128).
        group_size: Size of the groups for parameter reuse
         (default: -1, no grouping).
        activation_order: Whether to apply activation-order permutation
         (default: False).
        order_metric: Metric for ordering features
         (default: None, uses 1 / diag(invH)).
        compute_scale_zero: Function to compute scale and zero for
         quantization.

    Returns:
        quantized_weights: Quantized weight matrix [out_features, in_features].
        scale: float32. Scale parameters for quantization
         [out_features, num_groups].
        zero: Zero-point parameters for quantization [out_features, num_groups].
        g_idx: int32. Group indices for each feature [in_features].
    """
    in_features = ops.shape(weights_transpose)[1]

    if activation_order:
        # Use 1 / diag(inverse_hessian) as importance proxy by default.
        if order_metric is None:
            order_metric = ops.reciprocal(
                ops.add(ops.diagonal(inv_hessian), 1e-12)
            )
        else:
            # sanitize provided metric
            order_metric = ops.cast(order_metric, "float32")
            order_metric = ops.where(
                ops.isfinite(order_metric),
                order_metric,
                ops.zeros_like(order_metric),
            )
        # Sort in descending order by importance
        perm = _stable_permutation(order_metric)
        inv_perm = ops.argsort(perm)

        weights_transpose = ops.take(weights_transpose, perm, axis=1)
        inv_hessian = ops.take(
            ops.take(inv_hessian, perm, axis=0), perm, axis=1
        )
    else:
        perm = inv_perm = None

    # weights_buffer: [out_features, in_features]
    weights_buffer = weights_transpose
    # Buffer for the final quantized matrix: [out_features, in_features]
    quantized_weights_buffer = ops.zeros_like(weights_transpose, dtype="int32")

    scale_chunks = []
    zero_chunks = []

    # Compute effective group size
    effective_group = in_features if group_size == -1 else group_size

    # Process features in blocks
    for block_start in range(0, in_features, blocksize):
        block_end = min(block_start + blocksize, in_features)
        block_size = block_end - block_start

        # Block views
        # block_weights: [out_features, block_size]
        block_weights = weights_buffer[:, block_start:block_end]
        # block_error: [out_features, block_size]
        block_error = ops.zeros_like(block_weights)
        # block_inv_hessian: [block_size, block_size]
        block_inv_hessian = inv_hessian[
            block_start:block_end, block_start:block_end
        ]

        # Per-group cached params for reuse within the group
        cached_scale = None
        cached_zero = None
        cached_maxq = None
        cached_group_start = -1

        for block_idx in range(block_size):
            # Current global column index, represents the original column
            # in the weight matrix
            global_idx = block_start + block_idx
            # weight_column: [out_features,]
            weight_column = block_weights[:, block_idx]
            # Group-wise parameter reuse (compute once per group)
            if not effective_group == in_features:  # group_size != -1
                # Determine the group start index for the current column
                group_start = (global_idx // effective_group) * effective_group
                if group_start != cached_group_start:
                    # New group encountered, compute & cache params
                    # for this group
                    group_end = min(group_start + effective_group, in_features)
                    group_slice = weights_buffer[:, group_start:group_end]
                    cached_scale, cached_zero, cached_maxq = compute_scale_zero(
                        group_slice
                    )
                    # Store params once per group (in the order encountered).
                    scale_chunks.append(cached_scale)
                    zero_chunks.append(cached_zero)
                    cached_group_start = group_start
                scale, zero, maxq = cached_scale, cached_zero, cached_maxq
            else:
                # Single global group covering all columns.
                if cached_scale is None:
                    cached_scale, cached_zero, cached_maxq = compute_scale_zero(
                        weights_buffer
                    )
                    scale_chunks.append(cached_scale)
                    zero_chunks.append(cached_zero)
                    cached_group_start = 0
                scale, zero, maxq = cached_scale, cached_zero, cached_maxq

            # Quantize column and store it.
            # quantized_column: [out_features, 1]
            quantized_column = quantize_with_zero_point(
                ops.expand_dims(weight_column, 1), scale, zero, maxq
            )

            # Store quantized column in the buffer.
            quantized_weights_buffer = ops.slice_update(
                quantized_weights_buffer,
                (0, global_idx),
                ops.cast(quantized_column, "int32"),
            )
            # Dequantize column to compute error.
            # dequantized_col: [out_features,]
            dequantized_col = dequantize_with_zero_point(
                quantized_column, scale, zero
            )[:, 0]
            # Error feedback for remaining columns within the block
            # block_inv_hessian_diag: scalar
            current_block_influence = block_inv_hessian[block_idx, block_idx]
            # We divide by current_block_influence to get the
            # correct scaling of the error term.
            err = ops.divide(
                ops.subtract(weight_column, dequantized_col),
                current_block_influence,
            )
            # Record error for propagation to future blocks
            block_error = ops.slice_update(
                block_error, (0, block_idx), ops.expand_dims(err, 1)
            )

            # Update remaining columns in the current block
            # (those before the current column have already been quantized)
            # Propagate error to remaining columns in the block.
            if block_idx < block_size - 1:
                # update: [out_features, block_size - block_idx - 1]
                update = ops.matmul(
                    ops.expand_dims(err, 1),
                    ops.expand_dims(
                        block_inv_hessian[block_idx, block_idx + 1 :], 0
                    ),
                )
                # tail is a view of the remaining columns in the block
                # to be updated
                # tail: [out_features, block_size - block_idx - 1]
                tail = block_weights[:, block_idx + 1 :]
                block_weights = ops.slice_update(
                    block_weights,
                    (0, block_idx + 1),
                    ops.subtract(tail, update),
                )

        # Propagate block errors to future features (beyond the block)
        if block_end < in_features:
            # Total update for all future columns, based on the
            # accumulated error in this block. This is calculated
            # as the matrix product of the block_error and the
            # relevant slice of the inverse Hessian.
            # total_update: [out_features, in_features - block_end]
            total_update = ops.matmul(
                block_error, inv_hessian[block_start:block_end, block_end:]
            )
            # Update the remaining weights in the buffer. This is done
            # by subtracting the total_update from the remaining columns.
            weights_buffer = ops.concatenate(
                [
                    weights_buffer[:, :block_end],
                    ops.subtract(weights_buffer[:, block_end:], total_update),
                ],
                axis=1,
            )

    # Build group indices for each (possibly permuted) column
    # base_group = effective_group (int)
    base_group = effective_group

    # g_idx in permuted domain
    g_idx = ops.arange(0, in_features, dtype="int32")
    g_idx = ops.divide(g_idx, base_group)
    g_idx = ops.cast(g_idx, "float32")

    # Map group indices and quantized weights back to original column order
    if activation_order:
        g_idx = ops.take(g_idx, inv_perm, axis=0)
        quantized_weights_buffer = ops.take(
            quantized_weights_buffer, inv_perm, axis=1
        )

    # Concatenate recorded group params
    if len(scale_chunks) == 0:
        # Edge case: no groups recorded (empty input); fall back to whole matrix
        s, z, _ = compute_scale_zero(weights_transpose)
        scale = s
        zero = z
    else:
        scale = ops.concatenate(scale_chunks, axis=1)
        zero = ops.concatenate(zero_chunks, axis=1)

    return quantized_weights_buffer, scale, zero, g_idx