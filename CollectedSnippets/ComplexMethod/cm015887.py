def test_block_mask_device_change(self, device):
        device = torch.device(device)
        offset = torch.zeros(8, device=device)

        def causal_mask(b, h, q, kv):
            return (q + (offset[b] * 128)) >= kv

        block_mask = create_block_mask(causal_mask, 1, 1, 512, 512, device=device)
        if block_mask.kv_indices.device.type != device.type:
            raise AssertionError(
                f"Expected device type {device.type}, got {block_mask.kv_indices.device.type}"
            )
        if block_mask.kv_num_blocks.device.type != device.type:
            raise AssertionError(
                f"Expected device type {device.type}, got {block_mask.kv_num_blocks.device.type}"
            )
        if block_mask.q_indices.device.type != device.type:
            raise AssertionError(
                f"Expected device type {device.type}, got {block_mask.q_indices.device.type}"
            )
        if block_mask.q_num_blocks.device.type != device.type:
            raise AssertionError(
                f"Expected device type {device.type}, got {block_mask.q_num_blocks.device.type}"
            )

        block_mask = block_mask.to("cpu")
        if not block_mask.kv_indices.is_cpu:
            raise AssertionError("Expected kv_indices to be on CPU")
        if not block_mask.kv_num_blocks.is_cpu:
            raise AssertionError("Expected kv_num_blocks to be on CPU")
        if not block_mask.q_indices.is_cpu:
            raise AssertionError("Expected q_indices to be on CPU")
        if not block_mask.q_num_blocks.is_cpu:
            raise AssertionError("Expected q_num_blocks to be on CPU")

        block_mask = block_mask.to(device)
        if block_mask.kv_indices.device.type != device.type:
            raise AssertionError(
                f"Expected device type {device.type}, got {block_mask.kv_indices.device.type}"
            )
        if block_mask.kv_num_blocks.device.type != device.type:
            raise AssertionError(
                f"Expected device type {device.type}, got {block_mask.kv_num_blocks.device.type}"
            )
        if block_mask.q_indices.device.type != device.type:
            raise AssertionError(
                f"Expected device type {device.type}, got {block_mask.q_indices.device.type}"
            )
        if block_mask.q_num_blocks.device.type != device.type:
            raise AssertionError(
                f"Expected device type {device.type}, got {block_mask.q_num_blocks.device.type}"
            )