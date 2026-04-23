def test_weighted_percentile_array_api_consistency(
    global_random_seed,
    array_namespace,
    device_name,
    dtype_name,
    data,
    weights,
    percentile,
):
    """Check `_weighted_percentile` gives consistent results with array API."""
    xp, device = _array_api_for_tests(array_namespace, device_name)

    # Skip test for percentile=0 edge case (#20528) on namespace/device where
    # xp.nextafter is broken. This is the case for torch with MPS device:
    # https://github.com/pytorch/pytorch/issues/150027
    zero = xp.zeros(1, device=device)
    one = xp.ones(1, device=device)
    if percentile == 0 and xp.all(xp.nextafter(zero, one) == zero):
        pytest.xfail(f"xp.nextafter is broken on {device}")

    rng = np.random.RandomState(global_random_seed)
    X_np = data(rng) if callable(data) else data
    weights_np = weights(rng) if callable(weights) else weights
    # Ensure `data` of correct dtype
    X_np = X_np.astype(dtype_name)

    result_np = _weighted_percentile(X_np, weights_np, percentile)
    # Convert to Array API arrays
    X_xp = xp.asarray(X_np, device=device)
    weights_xp = xp.asarray(weights_np, device=device)

    with config_context(array_api_dispatch=True):
        result_xp = _weighted_percentile(X_xp, weights_xp, percentile)
        assert array_device(result_xp) == array_device(X_xp)
        assert get_namespace(result_xp)[0] == get_namespace(X_xp)[0]
        result_xp_np = move_to(result_xp, xp=np, device="cpu")

    assert result_xp_np.dtype == result_np.dtype
    assert result_xp_np.shape == result_np.shape
    assert_allclose(result_np, result_xp_np)

    # Check dtype correct (`sample_weight` should follow `array`)
    if dtype_name == "float32":
        assert result_xp_np.dtype == result_np.dtype == np.float32
    else:
        assert result_xp_np.dtype == np.float64