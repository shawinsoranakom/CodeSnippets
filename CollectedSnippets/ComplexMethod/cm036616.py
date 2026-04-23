def test_basic_rebalance():
    """Test basic rebalancing functionality"""
    # Example from https://github.com/deepseek-ai/eplb
    weight = torch.tensor(
        [
            [90, 132, 40, 61, 104, 165, 39, 4, 73, 56, 183, 86],
            [20, 107, 104, 64, 19, 197, 187, 157, 172, 86, 16, 27],
        ]
    )

    num_layers = weight.shape[0]
    num_replicas = 16
    num_groups = 4
    num_nodes = 2
    num_gpus = 8

    phy2log = DefaultEplbPolicy.rebalance_experts(
        weight, num_replicas, num_groups, num_nodes, num_gpus
    )
    log2phy, logcnt = compute_logical_maps(phy2log, weight.shape[-1])

    # Verify output shapes
    assert phy2log.shape == (
        2,
        16,
    ), f"Expected `phy2log` shape (2, 16), got {phy2log.shape}"
    assert log2phy.shape[0] == 2, (
        f"Expected `log2phy` first dimension 2, got {log2phy.shape[0]}"
    )
    assert log2phy.shape[1] == 12, (
        f"Expected `log2phy` second dimension 12, got {log2phy.shape[1]}"
    )
    assert logcnt.shape == (
        2,
        12,
    ), f"Expected `logcnt` shape (2, 12), got {logcnt.shape}"

    # Verify physical to logical expert mapping range is correct
    assert torch.all(phy2log >= 0) and torch.all(phy2log < 12), (
        "Physical to logical mapping should be in range [0, 12)"
    )

    # Verify expert count reasonableness
    assert torch.all(logcnt >= 1), "Each logical expert should have at least 1 replica"
    assert torch.sum(logcnt, dim=1).sum() == num_replicas * num_layers, (
        f"Total replicas should be {num_replicas * num_layers}"
    )

    # Verify expected output
    expected_phy2log = torch.tensor(
        [
            [5, 6, 5, 7, 8, 4, 3, 4, 10, 9, 10, 2, 0, 1, 11, 1],
            [7, 10, 6, 8, 6, 11, 8, 9, 2, 4, 5, 1, 5, 0, 3, 1],
        ]
    )
    assert torch.all(phy2log == expected_phy2log)

    expected_logcnt = torch.tensor(
        [[1, 2, 1, 1, 2, 2, 1, 1, 1, 1, 2, 1], [1, 2, 1, 1, 1, 2, 2, 1, 2, 1, 1, 1]]
    )
    assert torch.all(logcnt == expected_logcnt)