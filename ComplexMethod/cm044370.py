def test_ExponentialMovingAverage_init(data: np.ndarray, amount: float):
    """ Test that moving_average.MovingAverage correctly initializes """
    attrs = {"_data": np.ndarray,
             "_alpha": float,
             "_dtype": str,
             "_row_size": int,
             "_out": np.ndarray}

    instance = EMA(data, amount)
    # Verify required attributes exist and are of the correct type
    for attr, attr_type in attrs.items():
        assert attr in instance.__dict__
        assert isinstance(getattr(instance, attr), attr_type)
    # Verify we are testing all existing attributes
    for key in instance.__dict__:
        assert key in attrs

    # Verify numeric sanitization
    assert not np.any(np.isnan(instance._data))
    assert not np.any(np.isinf(instance._data))

    # Check alpha clamp logic
    expected_alpha = 1. - min(0.999, max(0.001, amount))
    assert instance._alpha == expected_alpha

    # dtype assignment logic
    expected_dtype = "float32" if data.dtype == np.float32 else "float64"
    assert instance._dtype == expected_dtype

    # ensure row size is positive and output matches shape and dtype
    assert instance._row_size > 0
    assert instance._out.shape == data.shape
    assert instance._out.dtype == expected_dtype