def test_getitem(self, device):
        offset = torch.zeros(8, device=device)

        def causal_mask(b, h, q, kv):
            return (q + (offset[b] * 128)) >= kv

        block_mask = create_block_mask(causal_mask, 4, 2, 512, 512, device=device)
        if block_mask.kv_num_blocks.shape != (4, 2, 4):
            raise AssertionError(
                f"Expected shape (4, 2, 4), got {block_mask.kv_num_blocks.shape}"
            )
        if block_mask.kv_indices.shape != (4, 2, 4, 4):
            raise AssertionError(
                f"Expected shape (4, 2, 4, 4), got {block_mask.kv_indices.shape}"
            )

        # Index on batch dimension
        new_block_mask = block_mask[0]
        if new_block_mask.kv_num_blocks.shape != (1, 2, 4):
            raise AssertionError(
                f"Expected shape (1, 2, 4), got {new_block_mask.kv_num_blocks.shape}"
            )
        if new_block_mask.kv_indices.shape != (1, 2, 4, 4):
            raise AssertionError(
                f"Expected shape (1, 2, 4, 4), got {new_block_mask.kv_indices.shape}"
            )

        # Index on batch and head dimension
        new_block_mask = block_mask[0, 1]
        if new_block_mask.kv_num_blocks.shape != (
            1,
            1,
            4,
        ):
            raise AssertionError(
                f"Expected shape (1, 1, 4), got {new_block_mask.kv_num_blocks.shape}"
            )
        if new_block_mask.kv_indices.shape != (1, 1, 4, 4):
            raise AssertionError(
                f"Expected shape (1, 1, 4, 4), got {new_block_mask.kv_indices.shape}"
            )

        # Index on batch and head dimension with -1 semantics
        new_block_mask = block_mask[-1, -2]
        if new_block_mask.kv_num_blocks.shape != (
            1,
            1,
            4,
        ):
            raise AssertionError(
                f"Expected shape (1, 1, 4), got {new_block_mask.kv_num_blocks.shape}"
            )
        if new_block_mask.kv_indices.shape != (1, 1, 4, 4):
            raise AssertionError(
                f"Expected shape (1, 1, 4, 4), got {new_block_mask.kv_indices.shape}"
            )

        # slicing on batch and head dimension
        new_block_mask = block_mask[0:2, 1:2]
        if new_block_mask.kv_num_blocks.shape != (2, 1, 4):
            raise AssertionError(
                f"Expected shape (2, 1, 4), got {new_block_mask.kv_num_blocks.shape}"
            )
        if new_block_mask.kv_indices.shape != (2, 1, 4, 4):
            raise AssertionError(
                f"Expected shape (2, 1, 4, 4), got {new_block_mask.kv_indices.shape}"
            )

        # slicing on batch, head, and query dimension
        new_block_mask = block_mask[0:2, 1:2, torch.tensor([1], dtype=torch.int32)]
        if new_block_mask.kv_num_blocks.shape != (2, 1, 1):
            raise AssertionError(
                f"Expected shape (2, 1, 1), got {new_block_mask.kv_num_blocks.shape}"
            )
        if new_block_mask.kv_indices.shape != (2, 1, 1, 4):
            raise AssertionError(
                f"Expected shape (2, 1, 1, 4), got {new_block_mask.kv_indices.shape}"
            )

        # slicing on batch, head, and query dimension
        q_index = torch.tensor([0], dtype=torch.int32)
        new_block_mask = block_mask[:, :, q_index]

        self.assertEqual(new_block_mask.kv_num_blocks.ndim, 3)
        self.assertEqual(new_block_mask.kv_indices.ndim, 4)
        torch.testing.assert_close(
            new_block_mask.kv_num_blocks,
            block_mask.kv_num_blocks[:, :, q_index],
        )
        torch.testing.assert_close(
            new_block_mask.kv_indices, block_mask.kv_indices[:, :, q_index, :]
        )

        if block_mask.full_kv_num_blocks is not None:
            if new_block_mask.full_kv_num_blocks is None:
                raise AssertionError("Expected full_kv_num_blocks to not be None")
            if new_block_mask.full_kv_indices is None:
                raise AssertionError("Expected full_kv_indices to not be None")
            torch.testing.assert_close(
                new_block_mask.full_kv_num_blocks,
                block_mask.full_kv_num_blocks[:, :, q_index],
            )
            torch.testing.assert_close(
                new_block_mask.full_kv_indices,
                block_mask.full_kv_indices[:, :, q_index, :],
            )