def from_kv_blocks(
        cls,
        kv_num_blocks: Tensor,
        kv_indices: Tensor,
        full_kv_num_blocks: Tensor | None = None,
        full_kv_indices: Tensor | None = None,
        BLOCK_SIZE: int | tuple[int, int] = _DEFAULT_SPARSE_BLOCK_SIZE,
        mask_mod: _mask_mod_signature | None = None,
        seq_lengths: tuple[int, int] | None = None,
        compute_q_blocks: bool = True,
    ) -> Self:
        """
        Creates a BlockMask instance from key-value block information.

        Args:
            kv_num_blocks (Tensor): Number of kv_blocks in each Q_BLOCK_SIZE row tile.
            kv_indices (Tensor): Indices of key-value blocks in each Q_BLOCK_SIZE row tile.
            full_kv_num_blocks (Optional[Tensor]): Number of full kv_blocks in each Q_BLOCK_SIZE row tile.
            full_kv_indices (Optional[Tensor]): Indices of full key-value blocks in each Q_BLOCK_SIZE row tile.
            BLOCK_SIZE (Union[int, tuple[int, int]]): Size of KV_BLOCK_SIZE x Q_BLOCK_SIZE tiles.
            mask_mod (Optional[Callable]): Function to modify the mask.

        Returns:
            BlockMask: Instance with full Q information generated via _transposed_ordered

        Raises:
            RuntimeError: If kv_indices has < 2 dimensions.
            AssertionError: If only one of full_kv_* args is provided.
        """
        if kv_indices.dim() < 2:
            raise RuntimeError("BlockMask must have at least 2 dimensions")

        if (full_kv_num_blocks is None) != (full_kv_indices is None):
            raise AssertionError(
                "full_kv_num_blocks and full_kv_indices must be both provided or omitted"
            )

        # Generate q_num_blocks and q_indices
        if compute_q_blocks:
            q_num_blocks, q_indices = _transpose_ordered(kv_num_blocks, kv_indices)
            if full_kv_num_blocks is not None:
                if full_kv_indices is None:
                    raise AssertionError("full_kv_indices must not be None")
                full_q_num_blocks, full_q_indices = _transpose_ordered(
                    full_kv_num_blocks, full_kv_indices
                )
            else:
                full_q_num_blocks, full_q_indices = None, None
        else:
            q_num_blocks, q_indices = None, None
            full_q_num_blocks, full_q_indices = None, None

        if isinstance(BLOCK_SIZE, int):
            BLOCK_SIZE = (BLOCK_SIZE, BLOCK_SIZE)

        mask_mod = mask_mod if mask_mod is not None else noop_mask
        if seq_lengths is None:
            q_length = kv_indices.shape[-2] * BLOCK_SIZE[0]
            kv_length = kv_indices.shape[-1] * BLOCK_SIZE[1]
            seq_lengths = (q_length, kv_length)

        return cls(
            seq_lengths=seq_lengths,
            kv_num_blocks=kv_num_blocks,
            kv_indices=kv_indices,
            full_kv_num_blocks=full_kv_num_blocks,
            full_kv_indices=full_kv_indices,
            q_num_blocks=q_num_blocks,
            q_indices=q_indices,
            full_q_num_blocks=full_q_num_blocks,
            full_q_indices=full_q_indices,
            BLOCK_SIZE=BLOCK_SIZE,
            mask_mod=mask_mod,
        )