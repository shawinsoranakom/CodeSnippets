def check_no_attributes_set_in_init(name, estimator_orig):
    """Check setting during init."""
    try:
        # Clone fails if the estimator does not store
        # all parameters as an attribute during init
        estimator = clone(estimator_orig)
    except AttributeError:
        raise AttributeError(
            f"Estimator {name} should store all parameters as an attribute during init."
        )

    init_params = _get_args(type(estimator).__init__)
    parents_init_params = [
        param
        for params_parent in (_get_args(parent) for parent in type(estimator).__mro__)
        for param in params_parent
    ]

    # Test for no setting apart from parameters during init
    invalid_attr = set(vars(estimator)) - set(init_params) - set(parents_init_params)
    # Ignore private attributes
    invalid_attr = set([attr for attr in invalid_attr if not attr.startswith("_")])
    assert not invalid_attr, (
        "Estimator %s should not set any attribute apart"
        " from parameters during init. Found attributes %s."
        % (name, sorted(invalid_attr))
    )