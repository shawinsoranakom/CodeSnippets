def _jagged_to_padded_dense_forward(
        jagged_values: TensorBox,
        jagged_offsets: list[TensorBox],
        max_lengths: list[int],  # list of ints/SymInts
        padding_value: float = 0.0,
    ) -> TensorBox:
        device = jagged_values.get_device_or_error()
        dtype = jagged_values.get_dtype()

        jagged_values_size = jagged_values.get_size()

        # only handle the common case of a single jagged dimension
        if (
            len(jagged_offsets) != 1
            or device.type != "cuda"
            or device != jagged_offsets[0].get_device()
            or len(jagged_values_size) != 2
            or len(jagged_offsets[0].get_size()) != 1
            or len(max_lengths) != len(jagged_offsets)
            or not is_integer_type(jagged_offsets[0])
        ):
            return fallback_handler(
                torch.ops.aten._jagged_to_padded_dense_forward.default,
                add_to_fallback_set=False,
            )(
                jagged_values,
                jagged_offsets,
                max_lengths,
                padding_value,
            )

        offsets: TensorBox = jagged_offsets[0]  # type: ignore[assignment]
        offsets_len = offsets.get_size()[0]
        offsets_dtype = offsets.get_dtype()
        batch_size = offsets_len - 1
        max_seq_len = max_lengths[0]
        embedding_len = jagged_values_size[1]
        jagged_len = jagged_values_size[0]

        output_size = [batch_size, max_seq_len, embedding_len]

        values_loader = jagged_values.make_loader()
        offsets_loader = offsets.make_loader()

        # pyre-ignore[2,3,53]
        def inner_fn(index):
            # dense tensor size: [B, N, D]
            batch_idx, seq_idx, emb_idx = index
            jagged_idx, end_idx = dense_idx_to_jagged_idx(
                batch_idx=batch_idx,
                seq_idx=seq_idx,
                offsets_loader=offsets_loader,
                jagged_len=jagged_len,
            )
            return ops.masked(
                ops.lt(
                    ops.index_expr(jagged_idx, offsets_dtype),
                    end_idx,
                ),
                lambda: values_loader([jagged_idx, emb_idx]),
                padding_value,
            )

        return Pointwise.create(
            device=device,
            dtype=dtype,
            inner_fn=inner_fn,
            ranges=output_size,
        )