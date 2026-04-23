def test_input_batch_with_kernel_block_sizes():
    """Test InputBatch initialization with kernel_block_sizes parameter."""
    max_num_reqs = 10
    max_model_len = 512
    max_num_batched_tokens = 512
    device = torch.device(DEVICE_TYPE)
    pin_memory = False
    vocab_size = 50272

    # Test with different kernel block sizes
    block_sizes = [32, 64]
    kernel_block_sizes = [16, 32]

    input_batch = InputBatch(
        max_num_reqs=max_num_reqs,
        max_model_len=max_model_len,
        max_num_batched_tokens=max_num_batched_tokens,
        device=device,
        pin_memory=pin_memory,
        vocab_size=vocab_size,
        block_sizes=block_sizes,
        kernel_block_sizes=kernel_block_sizes,
    )

    # Verify that block tables were created with kernel block sizes
    assert len(input_batch.block_table.block_tables) == len(block_sizes)

    for i, (kv_size, kernel_size) in enumerate(zip(block_sizes, kernel_block_sizes)):
        block_table = input_batch.block_table.block_tables[i]
        if kv_size != kernel_size:
            assert block_table.use_hybrid_blocks is True
            assert block_table.block_size == kernel_size
        else:
            assert block_table.use_hybrid_blocks is False
            assert block_table.block_size == kernel_size