def test_compute_logical_maps_with_negative_indices():
    """
    Test that compute_logical_maps correctly handles physical slots containing
    -1 (unused slots).
    """
    # 2 layers, 6 physical slots, 4 logical experts.
    # Slots 2 and 5 are unused (-1).
    phy2log = torch.tensor(
        [
            [0, 1, -1, 2, 3, -1],
            [3, -1, 2, 1, 0, -1],
        ]
    )
    num_layers = 2
    num_logical_experts = 4

    log2phy, logcnt = compute_logical_maps(phy2log, num_logical_experts)

    assert logcnt.shape == (num_layers, num_logical_experts)
    assert log2phy.shape == (num_layers, num_logical_experts, 1)

    expected_logcnt = torch.ones(num_layers, num_logical_experts, dtype=phy2log.dtype)
    assert torch.all(logcnt == expected_logcnt), (
        f"Expected that all replica counts == 1, got {logcnt}"
    )

    assert torch.all(log2phy >= 0), (
        "log2phy should only contain valid physical indices, not -1"
    )

    assert log2phy[0, 0, 0] == 0
    assert log2phy[0, 1, 0] == 1
    assert log2phy[0, 2, 0] == 3
    assert log2phy[0, 3, 0] == 4