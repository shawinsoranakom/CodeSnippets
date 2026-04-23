def _resolve_ray_search_alg(search_alg, task, space, iterations):
    """Resolve search algorithms and normalize Tune param_space for known Ray Tune searchers.

    Args:
        search_alg (str | object | None): The search algorithm to use. Can be a string name, a pre-instantiated Ray Tune
            searcher object, or None for default behavior.
        task (str): The task type (e.g., 'detect', 'segment', 'classify').
        space (dict): The hyperparameter search space.
        iterations (int): The maximum number of trials to run.

    Returns:
        (tuple): A tuple containing (resolved_search_alg, tuner_param_space, resolved_search_alg_kind).
            - resolved_search_alg: The configured searcher or None.
            - tuner_param_space: The normalized parameter space for the tuner.
            - resolved_search_alg_kind: The normalized algorithm name or None.

    Raises:
        ValueError: If an unsupported search_alg string is provided.
        ModuleNotFoundError: If required dependencies for the chosen algorithm are not installed.
    """
    if search_alg is None:
        return None, space, None

    normalized = _get_ray_search_alg_kind(search_alg)
    if isinstance(search_alg, str):
        if not normalized:
            return None, space, None
        if normalized not in RAY_SEARCH_ALG_REQUIREMENTS:
            supported = ", ".join(sorted(RAY_SEARCH_ALG_REQUIREMENTS))
            raise ValueError(f"Unsupported Ray Tune search_alg '{search_alg}'. Supported values: {supported}.")
        if normalized == "random":
            return None, space, normalized

    try:
        if normalized == "ax":
            if isinstance(search_alg, str):
                return _create_ax_search(space, task), {}, normalized
            _validate_ax_search_space(space)
            return search_alg, {}, normalized
        if normalized == "bohb":
            if isinstance(search_alg, str):
                resolved_search_alg, tuner_param_space = _create_bohb_search(space, task)
            else:
                _, tuner_param_space = _convert_bohb_search_space(space)
                resolved_search_alg = search_alg
            return resolved_search_alg, tuner_param_space, normalized
        if normalized == "nevergrad":
            return _create_nevergrad_search(task), space, normalized
        if normalized == "zoopt":
            if isinstance(search_alg, str):
                resolved_search_alg, tuner_param_space = _create_zoopt_search(space, task, iterations)
            else:
                _, tuner_param_space = _convert_zoopt_search_space(space)
                resolved_search_alg = search_alg
            return resolved_search_alg, tuner_param_space, normalized
        if not isinstance(search_alg, str):
            return search_alg, space, None

        requirements = RAY_SEARCH_ALG_REQUIREMENTS[normalized]
        if requirements:
            checks.check_requirements(requirements)

        from ray.tune.search import create_searcher

        return create_searcher(normalized, metric=TASK2METRIC[task], mode="max"), space, normalized
    except (ImportError, ModuleNotFoundError) as e:
        raise ModuleNotFoundError(
            f"Ray Tune search_alg '{search_alg}' requires additional dependencies. Original error: {e}"
        ) from e