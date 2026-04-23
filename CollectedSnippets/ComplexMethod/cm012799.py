def recheck_autotune_cache(
        self, reload_kernel_from_src: Callable[[], CachingAutotuner]
    ) -> None:
        """
        On cache load on static autotuner, we need to recheck the autotune cache, since
        a best config could have been found from a previous run
        """
        assert self.is_statically_launchable()

        configs = [result.config for result in self.compile_results]

        (cached_configs, _, autotune_cache_info) = check_autotune_cache(
            configs, self.filename, self.inductor_meta
        )
        self.autotune_cache_info = autotune_cache_info
        # I.e. there was an autotune cache hit
        if len(cached_configs) == 1:
            best_config = cached_configs[0]
            found_by_coordesc = getattr(best_config, "found_by_coordesc", False)
            # Grab the best compiled config, if it's in the list of available ones
            best_config_hash = triton_config_to_hashable(best_config)

            for compile_result in self.compile_results:
                if triton_config_to_hashable(compile_result.config) == best_config_hash:
                    compile_result.config.found_by_coordesc = found_by_coordesc
                    self.compile_results = [compile_result]
                    return

            # If the best config isn't in our list of compile results,
            # it's likely because it was found by coordesc after the cache
            # already saved
            if found_by_coordesc:
                with dynamo_timed("CachingAutotuner.slow_precompile_config"):
                    if self.fn.fn is None:
                        self.fn = reload_kernel_from_src().fn
                    self.compile_results = [self._precompile_config(best_config)]