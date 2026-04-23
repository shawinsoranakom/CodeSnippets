def prescreen_choices(
        choices: list[ChoiceCaller],
        name: str,
        inputs_key: str,
        prescreen_cache: dict[str, OrderedSet[str]],
    ) -> list[ChoiceCaller]:
        """
        Figure out what choices need to be prescreened before autotuning with runtime
        params.

        Prescreening is a process of reducing the number of autotuning for choices with
        runtime params via a two stage autotuning process. First, we fix a set of runtime
        params (here we use swizzle=2) and run autotuning to get a set of candidates.
        Then, we run autotuning again with the candidates and the full set of runtime
        params.

        Since have the concept of runtime params, we need to differentiate between
        choice's hash_key and choice's kernel_hash_key. The former includes information
        like runtime params, while the latter does not. prescreen_cache, if exists, stores
        the set of hash_key that should win the prescreening.

        Right now, only CUTLASS choices have runtime params.
        """
        # Create a cache key for prescreening results
        prescreen_key = f"{name}:{inputs_key}"

        # Check if we have cached prescreening results (prescreen_winners)
        if prescreen_key in prescreen_cache:
            prescreen_winners = [
                choice
                for choice in choices
                if choice.hash_key() in prescreen_cache[prescreen_key]
            ]
            return prescreen_winners

        # prescreen cutlass
        from .codegen.cutlass.kernel import CUTLASSTemplateCaller

        candidates = []
        if (
            config.cutlass.cutlass_prescreening
            and len(config.cutlass.cutlass_max_profiling_swizzle_options) > 1
        ):
            candidates.extend(
                [
                    c
                    for c in choices
                    if isinstance(c, CUTLASSTemplateCaller)
                    # hardcoded to only look at swizzle=2
                    if c.info_dict().get("swizzle") == "2"
                ]
            )

        # skip prescreening if the number of candidates is too small
        if len(candidates) < 10:
            return []

        # Include ATen in prescreening as fallback (#171094)
        extern_choices = [c for c in choices if isinstance(c, ExternKernelCaller)]
        candidates = extern_choices + candidates

        return candidates