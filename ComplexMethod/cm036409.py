def test_reduce():
    """Test that reduce() correctly reduces all nested connector stats."""
    stats = OffloadingConnectorStats(
        data={
            "CPU_to_GPU": [
                {"op_size": 16, "op_time": 1.0},
                {"op_size": 8, "op_time": 0.5},
                {"op_size": 3, "op_time": 0.2},
                {"op_size": 7, "op_time": 0.9},
            ],
            "GPU_to_CPU": [
                {"op_size": 1, "op_time": 0.1},
                {"op_size": 2, "op_time": 0.2},
                {"op_size": 16, "op_time": 2},
            ],
        }
    )

    reduced = stats.reduce()

    assert isinstance(reduced, dict)
    # Check that the stats were reduced (should have aggregated values)
    assert "CPU_to_GPU_total_bytes" in reduced
    assert "CPU_to_GPU_total_time" in reduced
    assert "GPU_to_CPU_total_bytes" in reduced
    assert "GPU_to_CPU_total_time" in reduced
    assert reduced["CPU_to_GPU_total_bytes"] == 34
    assert reduced["CPU_to_GPU_total_time"] == 2.6
    assert reduced["GPU_to_CPU_total_time"] == 2.3
    assert reduced["GPU_to_CPU_total_bytes"] == 19