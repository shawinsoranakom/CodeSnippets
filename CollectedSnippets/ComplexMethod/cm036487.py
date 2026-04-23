def test_get_load_balance_assignment_cases(
    sizes,
    num_gpus,
    expected_shuffle_indices,
    expected_gpu_sample_counts,
    expected_grouped_sizes_per_gpu,
    test_description,
):
    """Test get_load_balance_assignment with various input cases."""
    result = get_load_balance_assignment(sizes, num_gpus=num_gpus)
    (shuffle_indices, gpu_sample_counts, grouped_sizes_per_gpu) = result

    # Common assertions for all cases
    assert len(shuffle_indices) == len(sizes)
    assert len(gpu_sample_counts) == num_gpus
    assert len(grouped_sizes_per_gpu) == num_gpus
    assert sum(gpu_sample_counts) == len(sizes)

    assert shuffle_indices == expected_shuffle_indices

    assert gpu_sample_counts == expected_gpu_sample_counts
    assert grouped_sizes_per_gpu == expected_grouped_sizes_per_gpu