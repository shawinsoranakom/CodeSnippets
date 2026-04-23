def do_prune_configs(  # type: ignore[no-untyped-def]
        autotuner: "TritonAutotunerType",
        early_config_prune: Callable | None,
        perf_model: Callable | None,
        top_k: float,
        configs: list,
        named_args: dict,
        kwargs: dict,
    ) -> list["TritonConfig"]:
        # Reimplement autotuner.prune_configs(...) here
        # see: https://github.com/triton-lang/triton/blob/e57b46897191b3b3061c78d0d60e58e94be565b6/python/triton/runtime/autotuner.py
        # We do this to avoid calling prune_configs, which in turn calls early_config_prune and perf_model
        # These are both user-defined functions which can contain side effects, so we want to sandbox them in Dynamo

        if early_config_prune:
            configs = early_config_prune(configs, named_args, **kwargs)

        if perf_model:
            # we assert top_k is a float before calling this
            if isinstance(top_k, float) and top_k <= 1.0:
                top_k = int(len(configs) * top_k)
            elif not isinstance(top_k, int):
                """
                Slice index must be an integer, SupportsIndex or None
                """
                raise TypeError(
                    "Error while pruning configs, top_k must be either 1) a float <= 1.0 or 2) an int"
                )
            if len(configs) > top_k:
                est_timing = [
                    (
                        config,
                        float(
                            perf_model(**named_args, **kwargs, **config.all_kwargs())
                        ),
                    )
                    for config in configs
                ]
                configs = [
                    config[0]
                    for config in sorted(est_timing, key=operator.itemgetter(1))[:top_k]
                ]
        return configs