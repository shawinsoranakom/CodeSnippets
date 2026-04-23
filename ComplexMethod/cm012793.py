def filter_reduction_configs_for_determinism(
    inductor_meta: dict[str, Any], configs: list[Config]
) -> list[Config]:
    """
    Filter configs for reduction so the numerics can be deterministic.

    Heuristics:
    - skip reduction configs with too small RBLOCK
    - skip reduction configs with XBLOCK==1 if we are confident it will not perform well
    - if there is a tie, pick the config with second largest RBLOCK
    - if there is still a tie, pick the config with second largest num_warps
    - if there is still a tie, pick the config with second largest XBLOCK
    """
    configs = unique_configs(configs)
    assert len(configs) > 0

    def _do_filter_due_to_inductor_config():
        return (
            inductor_meta.get("deterministic", False)
            or inductor_meta.get("force_filter_reduction_configs", False)
        ) or inductor_meta.get("are_deterministic_algorithms_enabled")

    if not _do_filter_due_to_inductor_config() or len(configs) == 1:
        # no filtering happening if NOT in deterministic mode
        return configs

    if log.isEnabledFor(logging.DEBUG):
        log.debug("reduction configs before filtering:")
        for c in configs:
            log.debug("%s", c)
            log.debug("")

    def _has_too_small_rblock(config):
        rblock = config.kwargs.get("R0_BLOCK")
        # too small RBLOCK is likely to be bad
        return rblock is not None and rblock <= 4

    def _nonpromising_xblock_1(config):
        # kernel like https://gist.github.com/shunting314/0b3281c087e79bc915fe45985ff9d7d5
        # without a load/store having contiguous rdim is unlikely to perform well with XBLOCK==1
        return config.kwargs["XBLOCK"] == 1 and not inductor_meta.get(
            "has_loadstore_with_contiguous_rdim", True
        )

    newconfigs = [*filter(lambda x: not _has_too_small_rblock(x), configs)]
    # accept the filtering only if there are configs left
    if len(newconfigs) > 0:
        configs = newconfigs

    newconfigs = [*filter(lambda x: not _nonpromising_xblock_1(x), configs)]
    if len(newconfigs) > 0:
        configs = newconfigs

    assert len(configs) > 0

    def _r0_block(c):
        return c.kwargs.get("R0_BLOCK", -1)

    def _xblock(c):
        return c.kwargs.get("XBLOCK", -1)

    def _num_warps(c):
        return c.num_warps

    def _pick_second_largest(accessor):
        nonlocal configs
        configs = sorted(configs, key=lambda x: accessor(x))
        if accessor(configs[0]) != accessor(configs[-1]):
            max_val = accessor(configs[-1])
            configs = [*filter(lambda x: accessor(x) != max_val, configs)]
            second_max_val = accessor(configs[-1])
            configs = [*filter(lambda x: accessor(x) == second_max_val, configs)]
        return configs

    def _pick_config():
        nonlocal configs
        assert len(configs) > 0
        if len(configs) == 1:
            return configs[0]

        # break tie by R0_BLOCK
        configs = _pick_second_largest(_r0_block)
        if len(configs) == 1:
            return configs[0]

        # break tie by num_warps
        configs = _pick_second_largest(_num_warps)
        if len(configs) == 1:
            return configs[0]

        # break tie by XBLOCK
        configs = _pick_second_largest(_xblock)

        # there is still a tie, pick the first one
        return configs[0]

    configs = [_pick_config()]

    if log.isEnabledFor(logging.DEBUG):
        log.debug("reduction configs after filtering:")
        for c in configs:
            log.debug("%s", c)
            log.debug("")
    return configs