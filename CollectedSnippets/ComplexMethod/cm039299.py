def check_recorded_metadata(obj, method, parent, split_params=tuple(), **kwargs):
    """Check whether the expected metadata is passed to the object's method.

    Parameters
    ----------
    obj : estimator object
        sub-estimator to check routed params for
    method : str
        sub-estimator's method where metadata is routed to, or otherwise in
        the context of metadata routing referred to as 'callee'
    parent : str
        the parent method which should have called `method`, or otherwise in
        the context of metadata routing referred to as 'caller'
    split_params : tuple, default=empty
        specifies any parameters which are to be checked as being a subset
        of the original values
    **kwargs : dict
        passed metadata
    """
    all_records = (
        getattr(obj, "_records", dict()).get(method, dict()).get(parent, list())
    )
    for record in all_records:
        # first check that the names of the metadata passed are the same as
        # expected. The names are stored as keys in `record`.
        assert set(kwargs.keys()) == set(record.keys()), (
            f"Expected {kwargs.keys()} vs {record.keys()}"
        )
        for key, value in kwargs.items():
            recorded_value = record[key]
            # The following condition is used to check for any specified parameters
            # being a subset of the original values
            if key in split_params and recorded_value is not None:
                assert np.isin(recorded_value, value).all()
            else:
                if isinstance(recorded_value, np.ndarray):
                    assert_array_equal(recorded_value, value)
                else:
                    assert recorded_value is value, (
                        f"Expected {recorded_value} vs {value}. Method: {method}"
                    )