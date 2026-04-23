def test_eagle_step_slot_mapping_kernel_exceeds_max():
    """Test fused kernel when position exceeds max_model_len."""
    device = torch.device(DEVICE_TYPE)
    batch_size = 4
    block_size = 16
    max_model_len = 100
    n_blocks_per_req = (max_model_len + block_size - 1) // block_size

    positions_1d = torch.tensor([50, 98, 99, 100], dtype=torch.int64, device=device)
    block_table_tensor = torch.randint(
        0, 100, (batch_size, n_blocks_per_req), dtype=torch.int32, device=device
    )
    seq_lens = torch.tensor([51, 99, 100, 101], dtype=torch.int32, device=device)

    out_clamped = torch.zeros(batch_size, dtype=torch.int64, device=device)
    out_slot = torch.zeros(batch_size, dtype=torch.int64, device=device)
    eagle_step_update_slot_mapping_and_metadata(
        positions_1d=positions_1d,
        block_table_tensor=block_table_tensor,
        seq_lens=seq_lens,
        block_size=block_size,
        max_model_len=max_model_len,
        out_clamped_positions=out_clamped,
        out_slot_mapping=out_slot,
    )

    assert out_clamped[0].item() == 51
    assert out_clamped[1].item() == 99
    assert out_clamped[2].item() == 0
    assert out_clamped[3].item() == 0
    assert out_slot[2].item() == PADDING_SLOT_ID
    assert out_slot[3].item() == PADDING_SLOT_ID
    assert seq_lens[2].item() == 1
    assert seq_lens[3].item() == 1