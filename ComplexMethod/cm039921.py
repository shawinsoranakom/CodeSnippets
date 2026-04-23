def _estimator_with_converted_arrays(estimator, converter):
    """Create a new estimator with converted array attributes.

    All attributes that are arrays will be converted using the provided converter.

    Parameters
    ----------
    estimator : Estimator
        Estimator to convert

    converter : callable
        Callable that takes an array attribute and returns the converted array.

    Returns
    -------
    new_estimator : Estimator
        A clone of the estimator with converted array attributes.
    """
    # Inline import to avoid circular import
    from sklearn.base import clone

    # Because we call this function recursively `estimator` might actually be an
    # attribute of an estimator and not an actual estimator object.
    estimator_type = type(estimator)

    if hasattr(estimator, "__sklearn_array_api_convert__") and not inspect.isclass(
        estimator
    ):
        return estimator.__sklearn_array_api_convert__(converter)

    if estimator_type is dict:
        return {
            k: _estimator_with_converted_arrays(v, converter)
            for k, v in estimator.items()
        }

    if estimator_type in (list, tuple, set, frozenset):
        return estimator_type(
            _estimator_with_converted_arrays(v, converter) for v in estimator
        )

    if hasattr(estimator, "__dlpack__") or isinstance(
        estimator, (numpy.ndarray, numpy.generic)
    ):
        return converter(estimator)

    if not hasattr(estimator, "get_params") or isinstance(estimator, type):
        return estimator

    new_estimator = clone(estimator)
    for key, attribute in vars(estimator).items():
        attribute = _estimator_with_converted_arrays(attribute, converter)
        setattr(new_estimator, key, attribute)
    return new_estimator