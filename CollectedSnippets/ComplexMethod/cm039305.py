def get_init_args(metaestimator_info, sub_estimator_consumes):
    """Get the init args for a metaestimator

    This is a helper function to get the init args for a metaestimator from
    the METAESTIMATORS list. It returns an empty dict if no init args are
    required.

    Parameters
    ----------
    metaestimator_info : dict
        The metaestimator info from METAESTIMATORS

    sub_estimator_consumes : bool
        Whether the sub-estimator consumes metadata or not.

    Returns
    -------
    kwargs : dict
        The init args for the metaestimator.

    (estimator, estimator_registry) : (estimator, registry)
        The sub-estimator and the corresponding registry.

    (scorer, scorer_registry) : (scorer, registry)
        The scorer and the corresponding registry.

    (cv, cv_registry) : (CV splitter, registry)
        The CV splitter and the corresponding registry.
    """
    # Avoid mutating the original init_args dict to keep the test execution
    # thread-safe.
    kwargs = metaestimator_info.get("init_args", {}).copy()
    estimator, estimator_registry = None, None
    scorer, scorer_registry = None, None
    cv, cv_registry = None, None
    if "estimator" in metaestimator_info:
        estimator_name = metaestimator_info["estimator_name"]
        estimator_registry = _Registry()
        sub_estimator_type = metaestimator_info["estimator"]
        if sub_estimator_consumes:
            if sub_estimator_type == "regressor":
                estimator = ConsumingRegressor(estimator_registry)
            elif sub_estimator_type == "classifier":
                estimator = ConsumingClassifier(estimator_registry)
            else:
                raise ValueError("Unpermitted `sub_estimator_type`.")  # pragma: nocover
        else:
            if sub_estimator_type == "regressor":
                estimator = NonConsumingRegressor()
            elif sub_estimator_type == "classifier":
                estimator = NonConsumingClassifier()
            else:
                raise ValueError("Unpermitted `sub_estimator_type`.")  # pragma: nocover
        kwargs[estimator_name] = estimator
    if "scorer_name" in metaestimator_info:
        scorer_name = metaestimator_info["scorer_name"]
        scorer_registry = _Registry()
        scorer = ConsumingScorer(registry=scorer_registry)
        kwargs[scorer_name] = scorer
    if "cv_name" in metaestimator_info:
        cv_name = metaestimator_info["cv_name"]
        cv_registry = _Registry()
        if metaestimator_info["metaestimator"] is TargetEncoder:
            cv = ConsumingSplitterInheritingFromGroupKFold(registry=cv_registry)
        else:
            cv = ConsumingSplitter(registry=cv_registry)
        kwargs[cv_name] = cv

    return (
        kwargs,
        (estimator, estimator_registry),
        (scorer, scorer_registry),
        (cv, cv_registry),
    )