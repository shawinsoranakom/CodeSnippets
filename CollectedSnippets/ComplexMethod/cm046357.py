def _convert_bohb_search_space(space):
    """Convert a Tune search space into BOHB-compatible ConfigSpace and fixed-only Tune param_space.

    Args:
        space (dict): The hyperparameter search space.

    Returns:
        (tuple): A tuple containing the ConfigSpace object and a dict of fixed parameters.

    Raises:
        ValueError: If the search space contains grid search parameters or unsupported samplers.
        ImportError: If required BOHB packages are not installed.
    """
    checks.check_requirements(RAY_SEARCH_ALG_REQUIREMENTS["bohb"])

    import ConfigSpace
    from ray.tune.search.sample import Categorical, Float, Integer, LogUniform, Quantized, Uniform
    from ray.tune.search.variant_generator import parse_spec_vars
    from ray.tune.utils import flatten_dict

    resolved_space = flatten_dict(space, prevent_delimiter=True)
    resolved_vars, domain_vars, grid_vars = parse_spec_vars(resolved_space)
    if grid_vars:
        raise ValueError("Grid search parameters cannot be automatically converted to a TuneBOHB search space.")

    cs = ConfigSpace.ConfigurationSpace()
    for path, domain in domain_vars:
        par = "/".join(str(p) for p in path)
        sampler = domain.get_sampler()
        if isinstance(sampler, Quantized):
            raise ValueError("TuneBOHB does not support quantized search spaces with the current ConfigSpace version.")

        if isinstance(domain, Float) and isinstance(sampler, (Uniform, LogUniform)):
            cs.add(
                ConfigSpace.UniformFloatHyperparameter(
                    par, lower=domain.lower, upper=domain.upper, log=isinstance(sampler, LogUniform)
                )
            )
        elif isinstance(domain, Integer) and isinstance(sampler, (Uniform, LogUniform)):
            upper = domain.upper - 1  # Tune integer search spaces are exclusive on the upper bound
            cs.add(
                ConfigSpace.UniformIntegerHyperparameter(
                    par, lower=domain.lower, upper=upper, log=isinstance(sampler, LogUniform)
                )
            )
        elif isinstance(domain, Categorical) and isinstance(sampler, Uniform):
            cs.add(ConfigSpace.CategoricalHyperparameter(par, choices=domain.categories))
        else:
            raise ValueError(
                f"TuneBOHB does not support parameters of type {type(domain).__name__} "
                f"with sampler type {type(domain.sampler).__name__}."
            )

    fixed_param_space = {"/".join(str(p) for p in path): value for path, value in resolved_vars}
    return cs, fixed_param_space