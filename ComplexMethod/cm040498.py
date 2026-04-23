def tensordot(x1, x2, axes=2):
    a = get_ov_output(x1)
    b = get_ov_output(x2)
    a, b = _align_operand_types(a, b, "tensordot()")

    rank_a = a.get_partial_shape().rank.get_length()
    rank_b = b.get_partial_shape().rank.get_length()

    if isinstance(axes, int):
        axes_a = list(range(rank_a - axes, rank_a))
        axes_b = list(range(axes))
    else:
        axes_a, axes_b = [
            list(ax) if isinstance(ax, (list, tuple)) else [ax] for ax in axes
        ]
        axes_a = [canonicalize_axis(i, rank_a) for i in axes_a]
        axes_b = [canonicalize_axis(i, rank_b) for i in axes_b]

    notin_a = [i for i in range(rank_a) if i not in axes_a]
    notin_b = [i for i in range(rank_b) if i not in axes_b]

    # Transpose so contraction axes are at the end of A and beginning of B
    a_transpose = ov_opset.transpose(
        a, ov_opset.constant(notin_a + axes_a, Type.i32)
    )
    b_transpose = ov_opset.transpose(
        b, ov_opset.constant(axes_b + notin_b, Type.i32)
    )

    # Calculate the product of the contraction dimensions
    shape_a = ov_opset.shape_of(a, Type.i32)
    contract_dims = ov_opset.gather(
        shape_a, ov_opset.constant(axes_a, Type.i32), 0
    )
    contract_size = ov_opset.reduce_prod(contract_dims, 0, keep_dims=True)

    # Reshape A to [-1, contract_size] and B to [contract_size, -1]
    a_2d = ov_opset.reshape(
        a_transpose,
        ov_opset.concat([ov_opset.constant([-1], Type.i32), contract_size], 0),
        False,
    )
    b_2d = ov_opset.reshape(
        b_transpose,
        ov_opset.concat([contract_size, ov_opset.constant([-1], Type.i32)], 0),
        False,
    )

    result = ov_opset.matmul(a_2d, b_2d, False, False)

    # Reconstruct final shape from free dimensions
    if not notin_a and not notin_b:
        # Scalar output case
        result = ov_opset.reshape(
            result, ov_opset.constant([], Type.i32), False
        )
    else:
        shape_b = ov_opset.shape_of(b, Type.i32)
        final_parts = []
        if notin_a:
            final_parts.append(
                ov_opset.gather(
                    shape_a, ov_opset.constant(notin_a, Type.i32), 0
                )
            )
        if notin_b:
            final_parts.append(
                ov_opset.gather(
                    shape_b, ov_opset.constant(notin_b, Type.i32), 0
                )
            )

        result = ov_opset.reshape(
            result, ov_opset.concat(final_parts, 0), False
        )

    return OpenVINOKerasTensor(result.output(0))