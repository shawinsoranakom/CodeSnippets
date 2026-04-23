def _combo_sequential_autotune(self, launcher, *args, **kwargs):
        """
        Chain block-size decisions for combo kernels: tune one group at a time,
        each step building on the previous winner.

        Phase 1: Tune block sizes with warps/stages fixed from the base config.
        Phase 2: Re-tune warps/stages with finalized block sizes.
        """
        combo_tuning_groups = self.inductor_meta.get("combo_tuning_groups")
        if not combo_tuning_groups:
            return launcher

        if self.fn.fn is None:
            assert hasattr(self, "_reload_kernel")
            self.fn = self._reload_kernel().fn

        signature_keys = OrderedSet(self.triton_meta["signature"])
        best_config = launcher.config
        current_kwargs = dict(best_config.kwargs)
        base_num_warps = best_config.num_warps
        base_num_stages = best_config.num_stages

        start_time = time.time_ns()
        best_time = self.bench(launcher, *args, **kwargs)
        counters["inductor"]["combo_autotune_bench"] += 1
        self.coordesc_tuner.cache_benchmark_result(launcher.config, best_time)
        log.debug(
            "  Phase 1 baseline: %s warps=%d time=%f",
            dict(current_kwargs),
            base_num_warps,
            best_time,
        )

        # Phase 1: Tune block sizes per sub-kernel (largest first).
        # warps/stages stay fixed at base config values.
        for gi, group in enumerate(combo_tuning_groups):
            member_indices = group["member_indices"]
            cfgs = group["configs"]
            skip_rblock = group["skip_rblock"]

            if len(cfgs) <= 1:
                log.debug("  Phase 1 group %d SK%s: 1 config, skip", gi, member_indices)
                continue

            log.debug(
                "  Phase 1 group %d SK%s: trying %d configs, current_kwargs=%s",
                gi,
                member_indices,
                len(cfgs),
                dict(current_kwargs),
            )
            for ci, cfg in enumerate(cfgs):
                trial_kwargs = dict(current_kwargs)
                for idx in member_indices:
                    _update_combo_kernel_kwargs(
                        trial_kwargs, cfg.kwargs, idx, skip_rblock, signature_keys
                    )

                if trial_kwargs == current_kwargs:
                    log.debug("    cfg[%d] skip (same as current)", ci)
                    continue

                trial_config = triton.Config(
                    trial_kwargs,
                    num_warps=base_num_warps,
                    num_stages=base_num_stages,
                )

                with self.lock:
                    trial_launcher = self._precompile_config(
                        trial_config
                    ).make_launcher()
                trial_time = self.bench(trial_launcher, *args, **kwargs)
                counters["inductor"]["combo_autotune_bench"] += 1
                self.coordesc_tuner.cache_benchmark_result(trial_config, trial_time)

                improved = trial_time < best_time
                log.debug(
                    "    cfg[%d] trial=%s time=%f%s",
                    ci,
                    dict(trial_kwargs),
                    trial_time,
                    " (BETTER)" if improved else "",
                )
                if improved:
                    best_time = trial_time
                    launcher = trial_launcher
                    current_kwargs = trial_kwargs

            log.debug(
                "  Phase 1 group %d winner: current_kwargs=%s",
                gi,
                dict(current_kwargs),
            )

        # Phase 2: Re-tune num_warps/num_stages with finalized block sizes.
        # Block sizes are now optimal — find the best warp/stage pair for them.
        warp_stage_candidates = self.inductor_meta.get("combo_warp_stage_candidates")
        log.debug(
            "  Phase 2: blocks=%s, trying %d warp/stage pairs",
            dict(current_kwargs),
            len(warp_stage_candidates),
        )
        best_warps = launcher.config.num_warps
        best_stages = launcher.config.num_stages
        for num_warps, num_stages in warp_stage_candidates:
            if num_warps == best_warps and num_stages == best_stages:
                log.debug(
                    "    warps=%d stages=%d skip (same as current)",
                    num_warps,
                    num_stages,
                )
                continue

            trial_config = triton.Config(
                dict(current_kwargs),
                num_warps=num_warps,
                num_stages=num_stages,
            )
            with self.lock:
                trial_launcher = self._precompile_config(trial_config).make_launcher()
            trial_time = self.bench(trial_launcher, *args, **kwargs)
            counters["inductor"]["combo_autotune_bench"] += 1
            self.coordesc_tuner.cache_benchmark_result(trial_config, trial_time)

            improved = trial_time < best_time
            log.debug(
                "    warps=%d stages=%d time=%f%s",
                num_warps,
                num_stages,
                trial_time,
                " (BETTER)" if improved else "",
            )
            if improved:
                best_time = trial_time
                launcher = trial_launcher
                best_warps = num_warps
                best_stages = num_stages

        log.debug(
            "Combo sequential autotune for %s: best config %s, time %f",
            self.fn.__name__,
            launcher.config,
            best_time,
        )
        launcher.config.found_by_combo_autotune = True
        self.autotune_time_taken_ns += time.time_ns() - start_time
        if self.save_cache_hook:
            self.save_cache_hook(launcher.config, self.autotune_time_taken_ns)
        return launcher