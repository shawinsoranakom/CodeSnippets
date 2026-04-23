def test_get_masked_input_and_mask():
    x = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])

    # base tp 1 case, no padding
    modified_x, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=0,
        org_vocab_end_index=8,
        added_vocab_start_index=8,
        added_vocab_end_index=12,
        num_org_vocab_padding=0,
    )
    assert torch.equal(x, modified_x)

    # tp 2 case, no padding
    modified_x_rank_0, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=0,
        org_vocab_end_index=4,
        added_vocab_start_index=8,
        added_vocab_end_index=10,
        num_org_vocab_padding=0,
    )
    modified_x_rank_1, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=4,
        org_vocab_end_index=8,
        added_vocab_start_index=10,
        added_vocab_end_index=12,
        num_org_vocab_padding=0,
    )
    assert torch.equal(
        modified_x_rank_0, torch.tensor([0, 1, 2, 3, 0, 0, 0, 0, 4, 5, 0, 0])
    )
    assert torch.equal(
        modified_x_rank_1, torch.tensor([0, 0, 0, 0, 0, 1, 2, 3, 0, 0, 4, 5])
    )

    # tp 4 case, no padding
    modified_x_rank_0, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=0,
        org_vocab_end_index=2,
        added_vocab_start_index=8,
        added_vocab_end_index=9,
        num_org_vocab_padding=0,
    )
    modified_x_rank_1, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=2,
        org_vocab_end_index=4,
        added_vocab_start_index=9,
        added_vocab_end_index=10,
        num_org_vocab_padding=0,
    )
    modified_x_rank_2, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=4,
        org_vocab_end_index=6,
        added_vocab_start_index=10,
        added_vocab_end_index=11,
        num_org_vocab_padding=0,
    )
    modified_x_rank_3, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=6,
        org_vocab_end_index=8,
        added_vocab_start_index=11,
        added_vocab_end_index=12,
        num_org_vocab_padding=0,
    )
    assert torch.equal(
        modified_x_rank_0, torch.tensor([0, 1, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0])
    )
    assert torch.equal(
        modified_x_rank_1, torch.tensor([0, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 0])
    )
    assert torch.equal(
        modified_x_rank_2, torch.tensor([0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0])
    )
    assert torch.equal(
        modified_x_rank_3, torch.tensor([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2])
    )

    # base tp 1 case, with padding
    modified_x, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=0,
        org_vocab_end_index=8,
        added_vocab_start_index=8,
        added_vocab_end_index=12,
        num_org_vocab_padding=2,
    )
    assert torch.equal(
        modified_x, torch.tensor([0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13])
    )

    # tp 2 case, with padding
    modified_x_rank_0, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=0,
        org_vocab_end_index=4,
        added_vocab_start_index=8,
        added_vocab_end_index=10,
        num_org_vocab_padding=2,
    )
    modified_x_rank_1, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=4,
        org_vocab_end_index=8,
        added_vocab_start_index=10,
        added_vocab_end_index=12,
        num_org_vocab_padding=2,
    )
    assert torch.equal(
        modified_x_rank_0, torch.tensor([0, 1, 2, 3, 0, 0, 0, 0, 6, 7, 0, 0])
    )
    assert torch.equal(
        modified_x_rank_1, torch.tensor([0, 0, 0, 0, 0, 1, 2, 3, 0, 0, 6, 7])
    )

    # tp 4 case, with padding
    modified_x_rank_0, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=0,
        org_vocab_end_index=2,
        added_vocab_start_index=8,
        added_vocab_end_index=9,
        num_org_vocab_padding=2,
    )
    modified_x_rank_1, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=2,
        org_vocab_end_index=4,
        added_vocab_start_index=9,
        added_vocab_end_index=10,
        num_org_vocab_padding=2,
    )
    modified_x_rank_2, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=4,
        org_vocab_end_index=6,
        added_vocab_start_index=10,
        added_vocab_end_index=11,
        num_org_vocab_padding=2,
    )
    modified_x_rank_3, _ = get_masked_input_and_mask(
        x,
        org_vocab_start_index=6,
        org_vocab_end_index=8,
        added_vocab_start_index=11,
        added_vocab_end_index=12,
        num_org_vocab_padding=2,
    )
    assert torch.equal(
        modified_x_rank_0, torch.tensor([0, 1, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0])
    )
    assert torch.equal(
        modified_x_rank_1, torch.tensor([0, 0, 0, 1, 0, 0, 0, 0, 0, 4, 0, 0])
    )
    assert torch.equal(
        modified_x_rank_2, torch.tensor([0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 4, 0])
    )
    assert torch.equal(
        modified_x_rank_3, torch.tensor([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 4])
    )