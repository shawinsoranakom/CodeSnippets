def test_connectivity(seed=36):
    # Test that graph connectivity test works as expected
    graph = np.array(
        [
            [1, 0, 0, 0, 0],
            [0, 1, 1, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 0, 1, 1, 1],
            [0, 0, 0, 1, 1],
        ]
    )
    assert not _graph_is_connected(graph)
    for csr_container in CSR_CONTAINERS:
        assert not _graph_is_connected(csr_container(graph))
    for csc_container in CSC_CONTAINERS:
        assert not _graph_is_connected(csc_container(graph))

    graph = np.array(
        [
            [1, 1, 0, 0, 0],
            [1, 1, 1, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 0, 1, 1, 1],
            [0, 0, 0, 1, 1],
        ]
    )
    assert _graph_is_connected(graph)
    for csr_container in CSR_CONTAINERS:
        assert _graph_is_connected(csr_container(graph))
    for csc_container in CSC_CONTAINERS:
        assert _graph_is_connected(csc_container(graph))