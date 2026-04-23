def no_overlapping(configs: list[dict]) -> list[dict]:
    """Validate that intervals are not overlapping.

    For a list of observations ensure that there are no overlapping intervals
    for NUMERIC_STATE observations for the same entity.
    """
    numeric_configs = [
        config for config in configs if config[CONF_PLATFORM] == CONF_NUMERIC_STATE
    ]
    if len(numeric_configs) < 2:
        return configs

    class NumericConfig(NamedTuple):
        above: float
        below: float

    d: dict[str, list[NumericConfig]] = {}
    for _, config in enumerate(numeric_configs):
        above = config.get(CONF_ABOVE, -math.inf)
        below = config.get(CONF_BELOW, math.inf)
        entity_id: str = str(config[CONF_ENTITY_ID])
        d.setdefault(entity_id, []).append(NumericConfig(above, below))

    for ent_id, intervals in d.items():
        intervals = sorted(intervals, key=lambda tup: tup.above)

        for i, tup in enumerate(intervals):
            if len(intervals) > i + 1 and tup.below > intervals[i + 1].above:
                _LOGGER.error(
                    "Ranges for bayesian numeric state entities must not overlap, but %s has overlapping ranges, above:%s, below:%s overlaps with above:%s, below:%s",
                    ent_id,
                    tup.above,
                    tup.below,
                    intervals[i + 1].above,
                    intervals[i + 1].below,
                )
                raise vol.Invalid(
                    "overlapping_ranges",
                )
    return configs