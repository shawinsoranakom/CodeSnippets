def test_additional_cases():
    """Test more edge cases and different parameter combinations"""

    # Test case 1: Large-scale distributed setup
    weight1 = torch.tensor(
        [[50, 100, 75, 120, 90, 60, 80, 110, 40, 70, 95, 85, 65, 55, 45, 35]]
    )
    phy2log1 = DefaultEplbPolicy.rebalance_experts(weight1, 24, 8, 4, 8)
    _, logcnt1 = compute_logical_maps(phy2log1, weight1.shape[-1])

    assert phy2log1.shape == (1, 24)
    assert logcnt1.shape == (1, 16)
    assert torch.sum(logcnt1) == 24

    # Test case 2: Different weight distributions
    weight2 = torch.tensor(
        [
            [200, 150, 100, 50, 25, 12],  # Decreasing weights
            [12, 25, 50, 100, 150, 200],  # Increasing weights
        ]
    )
    phy2log2 = DefaultEplbPolicy.rebalance_experts(weight2, 10, 3, 1, 2)
    _, logcnt2 = compute_logical_maps(phy2log2, weight2.shape[-1])

    assert phy2log2.shape == (2, 10)
    assert logcnt2.shape == (2, 6)

    # Verify high-weight experts have more replicas
    for layer in range(2):
        max_weight_idx = torch.argmax(weight2[layer])
        assert logcnt2[layer, max_weight_idx] >= 2