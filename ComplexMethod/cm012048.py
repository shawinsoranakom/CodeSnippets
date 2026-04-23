def _dense_to_jagged_forward_impl(
        fallback_op,  # pyre-ignore[2]
        dense: TensorBox,
        jagged_offsets: list[TensorBox],
        jagged_len: int | None = None,
    ) -> TensorBox:
        device = dense.get_device_or_error()
        dtype = dense.get_dtype()

        dense_size = dense.get_size()

        # only handle the common case of a single jagged dimension
        if (
            len(jagged_offsets) != 1
            or device.type != "cuda"
            or device != jagged_offsets[0].get_device()
            or len(jagged_offsets[0].get_size()) != 1
            or len(dense_size) != 3
            or jagged_len is None
            or not is_integer_type(jagged_offsets[0])
        ):
            return fallback_handler(fallback_op, add_to_fallback_set=False)(
                dense,
                jagged_offsets,
                jagged_len,
            )

        offsets: TensorBox = jagged_offsets[0]  # type: ignore[assignment]
        offsets_dtype = offsets.get_dtype()
        batch_size = dense_size[0]
        max_seq_len = dense_size[1]
        embedding_len = dense_size[-1]

        output_size = [jagged_len, embedding_len]

        dense_loader = dense.make_loader()
        offsets_loader = offsets.make_loader()

        inverse_offsets = get_inverse_offsets(
            offsets=offsets,
            jagged_len=jagged_len,
        )
        inverse_offsets_loader = inverse_offsets.make_loader()

        # pyre-ignore[2,3,53]
        def inner_fn(index):
            # jagged tensor size: [sum_B(N_B), D]
            jagged_idx, emb_idx = index
            batch_idx, seq_idx = jagged_idx_to_dense_idx(
                jagged_idx=jagged_idx,
                offsets_loader=offsets_loader,
                inverse_offsets_loader=inverse_offsets_loader,
                batch_size=batch_size,
                max_seq_len=max_seq_len,
                offsets_dtype=offsets_dtype,
            )
            return ops.masked(
                ops.lt(
                    ops.index_expr(seq_idx, offsets_dtype),
                    ops.index_expr(max_seq_len, offsets_dtype),
                ),
                lambda: dense_loader([batch_idx, seq_idx, emb_idx]),
                0.0,  # jagged sequence longer than max_seq_len
            )

        return Pointwise.create(
            device=device,
            dtype=dtype,
            inner_fn=inner_fn,
            ranges=output_size,
        )