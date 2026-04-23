def unique(
    x,
    sorted=True,
    return_inverse=False,
    return_counts=False,
    axis=None,
    size=None,
    fill_value=None,
):
    x = get_ov_output(x)
    # OpenVINO Unique with sorted=False may produce unstable values on CPU.
    # Keep outputs deterministic and correct by always requesting sorted values.
    ov_sorted = True
    x_shape = ov_opset.shape_of(x, Type.i32).output(0)
    x_rank = x.get_partial_shape().rank.get_length()

    if axis is None:
        x_flat = ov_opset.reshape(
            x, ov_opset.constant([-1], Type.i32).output(0), False
        ).output(0)
        x_flat_pshape = x_flat.get_partial_shape()
        if (
            x_flat_pshape.rank.is_static
            and x_flat_pshape[0].is_static
            and x_flat_pshape[0].get_length() == 0
        ):
            values = x_flat
            inverse = ov_opset.constant(np.array([], dtype=np.int32)).output(0)
            counts = ov_opset.constant(np.array([], dtype=np.int32)).output(0)
            dim = 0
        else:
            x_type = x_flat.get_element_type()

            if x_type.is_real():
                nan_mask = ov_opset.not_equal(x_flat, x_flat).output(0)
                n = ov_opset.squeeze(
                    ov_opset.shape_of(x_flat, Type.i32).output(0),
                    ov_opset.constant([0], Type.i32).output(0),
                ).output(0)
                idx = ov_opset.range(
                    ov_opset.constant(0, Type.i32).output(0),
                    n,
                    ov_opset.constant(1, Type.i32).output(0),
                    output_type=Type.i32,
                ).output(0)
                idx_as_x = ov_opset.convert(idx, x_type).output(0)

                payload = ov_opset.select(nan_mask, idx_as_x, x_flat).output(0)
                nan_tag = ov_opset.convert(nan_mask, x_type).output(0)
                rows = ov_opset.concat(
                    [
                        ov_opset.unsqueeze(
                            nan_tag,
                            ov_opset.constant([1], Type.i32).output(0),
                        ).output(0),
                        ov_opset.unsqueeze(
                            payload,
                            ov_opset.constant([1], Type.i32).output(0),
                        ).output(0),
                    ],
                    axis=1,
                ).output(0)

                uniq = ov_opset.unique(
                    rows,
                    axis=ov_opset.constant(0, Type.i32).output(0),
                    sorted=ov_sorted,
                    index_element_type="i32",
                    count_element_type="i32",
                )
                uniq_rows = uniq.output(0)
                inverse = uniq.output(2)
                counts = uniq.output(3)

                uniq_nan_tag = ov_opset.squeeze(
                    ov_opset.gather(
                        uniq_rows,
                        ov_opset.constant([0], Type.i32).output(0),
                        ov_opset.constant(1, Type.i32).output(0),
                    ).output(0),
                    ov_opset.constant([1], Type.i32).output(0),
                ).output(0)
                uniq_payload = ov_opset.squeeze(
                    ov_opset.gather(
                        uniq_rows,
                        ov_opset.constant([1], Type.i32).output(0),
                        ov_opset.constant(1, Type.i32).output(0),
                    ).output(0),
                    ov_opset.constant([1], Type.i32).output(0),
                ).output(0)

                nan_mask_u = ov_opset.convert(
                    uniq_nan_tag, Type.boolean
                ).output(0)
                nan_const = ov_opset.constant(np.nan, x_type).output(0)
                values = ov_opset.select(
                    nan_mask_u, nan_const, uniq_payload
                ).output(0)
            else:
                uniq = ov_opset.unique(
                    x_flat,
                    sorted=ov_sorted,
                    index_element_type="i32",
                    count_element_type="i32",
                )
                values = uniq.output(0)
                inverse = uniq.output(2)
                counts = uniq.output(3)
            dim = 0
    else:
        dim = axis + x_rank if axis < 0 else axis
        axis_node = ov_opset.constant(dim, Type.i32).output(0)
        dim_len_is_zero = False
        x_pshape = x.get_partial_shape()
        if (
            x_pshape.rank.is_static
            and x_pshape[dim].is_static
            and x_pshape[dim].get_length() == 0
        ):
            dim_len_is_zero = True
        if dim_len_is_zero:
            values = x
            inverse = ov_opset.constant(np.array([], dtype=np.int32)).output(0)
            counts = ov_opset.constant(np.array([], dtype=np.int32)).output(0)
        else:
            uniq = ov_opset.unique(
                x,
                axis=axis_node,
                sorted=ov_sorted,
                index_element_type="i32",
                count_element_type="i32",
            )
            values = uniq.output(0)
            inverse = uniq.output(2)
            counts = uniq.output(3)

    if size is not None:
        values_shape = ov_opset.shape_of(values, Type.i32).output(0)
        values_count = ov_opset.squeeze(
            ov_opset.gather(
                values_shape,
                ov_opset.constant([dim], Type.i32).output(0),
                ov_opset.constant(0, Type.i32).output(0),
            ).output(0),
            ov_opset.constant([0], Type.i32).output(0),
        ).output(0)

        size_node = ov_opset.constant(size, Type.i32).output(0)
        trunc_size = ov_opset.minimum(values_count, size_node).output(0)

        trunc_idx = ov_opset.range(
            ov_opset.constant(0, Type.i32).output(0),
            trunc_size,
            ov_opset.constant(1, Type.i32).output(0),
            output_type=Type.i32,
        ).output(0)
        values = ov_opset.gather(
            values,
            trunc_idx,
            ov_opset.constant(dim, Type.i32).output(0),
        ).output(0)

        pad_amount = ov_opset.maximum(
            ov_opset.subtract(size_node, values_count).output(0),
            ov_opset.constant(0, Type.i32).output(0),
        ).output(0)

        if dim == 0:
            values_shape_after_trunc = ov_opset.shape_of(
                values, Type.i32
            ).output(0)
            tail_shape = ov_opset.slice(
                values_shape_after_trunc,
                ov_opset.constant([1], Type.i32).output(0),
                ov_opset.constant([2**31 - 1], Type.i32).output(0),
                ov_opset.constant([1], Type.i32).output(0),
            ).output(0)
            pad_shape = ov_opset.concat(
                [
                    ov_opset.unsqueeze(
                        pad_amount,
                        ov_opset.constant([0], Type.i32).output(0),
                    ).output(0),
                    tail_shape,
                ],
                axis=0,
            ).output(0)
            fill = 0 if fill_value is None else fill_value
            fill_node = get_ov_output(fill, values.get_element_type())
            pad_block = ov_opset.broadcast(fill_node, pad_shape).output(0)
            values = ov_opset.concat([values, pad_block], axis=0).output(0)
        else:
            perm = [dim] + [i for i in range(x_rank) if i != dim]
            inv_perm = [0] * x_rank
            for i, p in enumerate(perm):
                inv_perm[p] = i

            values_t = ov_opset.transpose(
                values,
                ov_opset.constant(perm, Type.i32).output(0),
            ).output(0)
            values_t_shape = ov_opset.shape_of(values_t, Type.i32).output(0)
            tail_shape = ov_opset.slice(
                values_t_shape,
                ov_opset.constant([1], Type.i32).output(0),
                ov_opset.constant([2**31 - 1], Type.i32).output(0),
                ov_opset.constant([1], Type.i32).output(0),
            ).output(0)
            pad_shape = ov_opset.concat(
                [
                    ov_opset.unsqueeze(
                        pad_amount,
                        ov_opset.constant([0], Type.i32).output(0),
                    ).output(0),
                    tail_shape,
                ],
                axis=0,
            ).output(0)
            fill = 0 if fill_value is None else fill_value
            fill_node = get_ov_output(fill, values_t.get_element_type())
            pad_block = ov_opset.broadcast(fill_node, pad_shape).output(0)
            values_t = ov_opset.concat([values_t, pad_block], axis=0).output(0)
            values = ov_opset.transpose(
                values_t,
                ov_opset.constant(inv_perm, Type.i32).output(0),
            ).output(0)

        if return_counts:
            counts = ov_opset.gather(
                counts,
                trunc_idx,
                ov_opset.constant(0, Type.i32).output(0),
            ).output(0)
            zero_counts = ov_opset.constant(
                0, counts.get_element_type()
            ).output(0)
            counts_pad = ov_opset.broadcast(
                zero_counts,
                ov_opset.unsqueeze(
                    pad_amount,
                    ov_opset.constant([0], Type.i32).output(0),
                ).output(0),
            ).output(0)
            counts = ov_opset.concat([counts, counts_pad], axis=0).output(0)

    if return_inverse and axis is None:
        inverse = ov_opset.reshape(inverse, x_shape, False).output(0)

    outputs = [OpenVINOKerasTensor(values)]
    if return_inverse:
        outputs.append(OpenVINOKerasTensor(inverse))
    if return_counts:
        outputs.append(OpenVINOKerasTensor(counts))

    return outputs[0] if len(outputs) == 1 else tuple(outputs)