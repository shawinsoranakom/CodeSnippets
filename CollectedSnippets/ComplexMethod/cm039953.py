def test_weighted_percentile_2d(global_random_seed, percentile_rank, average):
    """Check `_weighted_percentile` behaviour is correct when `array` is 2D."""
    # Check for when array 2D and sample_weight 1D
    rng = np.random.RandomState(global_random_seed)
    x1 = rng.randint(10, size=10)
    w1 = rng.choice(5, size=10)

    x2 = rng.randint(20, size=10)
    x_2d = np.vstack((x1, x2)).T

    wp = _weighted_percentile(
        x_2d, w1, percentile_rank=percentile_rank, average=average
    )

    if isinstance(percentile_rank, list):
        p_list = []
        for pr in percentile_rank:
            p_list.append(
                [
                    _weighted_percentile(
                        x_2d[:, i], w1, percentile_rank=pr, average=average
                    )
                    for i in range(x_2d.shape[1])
                ]
            )
        p_axis_0 = np.stack(p_list, axis=-1)
        assert wp.shape == (x_2d.shape[1], len(percentile_rank))
    else:
        # percentile_rank is scalar
        p_axis_0 = [
            _weighted_percentile(
                x_2d[:, i], w1, percentile_rank=percentile_rank, average=average
            )
            for i in range(x_2d.shape[1])
        ]
        assert wp.shape == (x_2d.shape[1],)

    assert_allclose(wp, p_axis_0)

    # Check when array and sample_weight both 2D
    w2 = rng.choice(5, size=10)
    w_2d = np.vstack((w1, w2)).T

    wp = _weighted_percentile(
        x_2d, w_2d, percentile_rank=percentile_rank, average=average
    )

    if isinstance(percentile_rank, list):
        p_list = []
        for pr in percentile_rank:
            p_list.append(
                [
                    _weighted_percentile(
                        x_2d[:, i], w_2d[:, i], percentile_rank=pr, average=average
                    )
                    for i in range(x_2d.shape[1])
                ]
            )
        p_axis_0 = np.stack(p_list, axis=-1)
        assert wp.shape == (x_2d.shape[1], len(percentile_rank))
    else:
        # percentile_rank is scalar
        p_axis_0 = [
            _weighted_percentile(
                x_2d[:, i], w_2d[:, i], percentile_rank=percentile_rank, average=average
            )
            for i in range(x_2d.shape[1])
        ]
        assert wp.shape == (x_2d.shape[1],)

    assert_allclose(wp, p_axis_0)