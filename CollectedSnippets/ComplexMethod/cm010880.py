def _get_custom_estimator_solver_uuids(
    autograd_config: Any,
) -> tuple[object | None, object | None]:
    """
    Extract uuid values from custom runtime estimator and solver configs if they have uuid() methods.

    Returns a tuple of (runtime_estimator_uuid, solver_uuid).

    Returns None for each component if:
    - The config field value is None
    - The config field value is a string (built-in option like "flops", "greedy")

    Raises BypassAOTAutogradCache if:
    - The config field value is a raw callable without uuid() method (caching not supported)
    - The CustomRuntimeEstimator/CustomKnapsackSolver's uuid() method returns None
    (caching explicitly disabled by implementation)
    """

    runtime_estimator = getattr(
        autograd_config, "activation_memory_budget_runtime_estimator", None
    )
    solver = getattr(autograd_config, "activation_memory_budget_solver", None)

    runtime_estimator_uuid = None
    solver_uuid = None

    if isinstance(runtime_estimator, CustomRuntimeEstimator):
        runtime_estimator_uuid = runtime_estimator.uuid()
        if runtime_estimator_uuid is None:
            raise BypassAOTAutogradCache(
                "CustomRuntimeEstimator.uuid() returned None, bypassing cache"
            )
    elif callable(runtime_estimator) and not isinstance(runtime_estimator, str):
        raise BypassAOTAutogradCache(
            "activation_memory_budget_runtime_estimator is a raw callable without uuid() method, "
            "bypassing cache. Use CustomRuntimeEstimator for cache support."
        )

    if isinstance(solver, CustomKnapsackSolver):
        solver_uuid = solver.uuid()
        if solver_uuid is None:
            raise BypassAOTAutogradCache(
                "CustomKnapsackSolver.uuid() returned None, bypassing cache"
            )
    elif callable(solver) and not isinstance(solver, str):
        raise BypassAOTAutogradCache(
            "activation_memory_budget_solver is a raw callable without uuid() method, "
            "bypassing cache. Use CustomKnapsackSolver for cache support."
        )

    return runtime_estimator_uuid, solver_uuid