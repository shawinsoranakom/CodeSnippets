def get_random_distribution(
    conf: dict, section: str, subsection: str, optional: bool = False
) -> Distribution:
    # section can be "prompt_input" or "prompt_output" (both required)
    conf = conf[section]

    if optional and subsection not in conf:
        # Optional subsection, if not found assume the value is always 0
        return ConstantDistribution(0)

    # subsection can be "num_turns", "num_tokens" or "prefix_num_tokens"
    if subsection not in conf:
        raise ValueError(f"Missing subsection {subsection} in section {section}")

    conf = conf[subsection]

    distribution = conf.get("distribution")
    if distribution is None:
        raise ValueError(
            f"Missing field 'distribution' in {section=} and {subsection=}"
        )

    if distribution == "constant":
        verify_field_exists(conf, "value", section, subsection)
        return ConstantDistribution(conf["value"])

    elif distribution == "zipf":
        verify_field_exists(conf, "alpha", section, subsection)
        max_val = conf.get("max", None)
        return ZipfDistribution(conf["alpha"], max_val=max_val)

    elif distribution == "poisson":
        verify_field_exists(conf, "alpha", section, subsection)
        max_val = conf.get("max", None)
        return PoissonDistribution(conf["alpha"], max_val=max_val)

    elif distribution == "lognormal":
        max_val = conf.get("max", None)

        if "average" in conf:
            # Infer lognormal mean/sigma (numpy) from input average
            median_ratio = conf.get("median_ratio", None)
            return LognormalDistribution(
                average=conf["average"], median_ratio=median_ratio, max_val=max_val
            )

        # Use mean/sigma directly (for full control over the distribution)
        verify_field_exists(conf, "mean", section, subsection)
        verify_field_exists(conf, "sigma", section, subsection)
        return LognormalDistribution(
            mean=conf["mean"], sigma=conf["sigma"], max_val=max_val
        )

    elif distribution == "uniform":
        verify_field_exists(conf, "min", section, subsection)
        verify_field_exists(conf, "max", section, subsection)

        min_value = conf["min"]
        max_value = conf["max"]

        assert min_value > 0
        assert min_value <= max_value

        is_integer = isinstance(min_value, int) and isinstance(max_value, int)
        return UniformDistribution(min_value, max_value, is_integer)
    else:
        raise ValueError(f"Unknown distribution: {distribution}")