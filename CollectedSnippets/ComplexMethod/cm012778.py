def autotune(
        self,
        # pyrefly: ignore [missing-attribute]
        func: Callable[["triton.Config"], float],
        # pyrefly: ignore [missing-attribute]
        baseline_config: "triton.Config",
        baseline_timing: float | None = None,
    ) -> "triton.Config":  # pyrefly: ignore  # missing-attribute
        """
        Perform coordinate descent autotuning starting from a baseline configuration.
        """
        if baseline_timing is None:
            baseline_timing = self.call_func(func, baseline_config)

        log.debug("= Do coordinate descent tuning for %s =", self.name)
        log.debug(
            "%s: Baseline Config %s, baseline timing %f",
            self.name,
            baseline_config,
            baseline_timing,
        )
        improved = True
        best_config = baseline_config
        best_timing = baseline_timing

        self._combo_tunable_fields = self.inductor_meta.get(
            "combo_coordesc_field_order", []
        )

        tunable_fields = self.tunable_fields

        while improved:
            improved = False

            for name in tunable_fields:
                cur_val = get_field(best_config, name)
                # some kernel don't have R0_BLOCK/YBLOCK/ZBLOCK. So cur_val may be None
                if cur_val is None:
                    continue

                # It's possible that candidate_values is empty.
                # E.g., if XBLOCK is 1 initially and size_hint for x is also 1.
                # We would not try either larger or smaller XBLOCK in this case.
                candidate_values = self.get_neighbour_values(name, cur_val)

                for next_val in candidate_values:
                    candidate_config = copy.deepcopy(best_config)
                    set_field(candidate_config, name, next_val)

                    if not self.is_valid_config(candidate_config):
                        continue
                    cmp_res, candidate_timing = self.compare_config(
                        func, candidate_config, best_config, best_timing
                    )
                    if cmp_res:
                        improved = True
                        best_config, best_timing = candidate_config, candidate_timing

            if not improved and self.inductor_meta.get(
                "coordinate_descent_check_all_directions"
            ):
                old_best_timing = best_timing
                improved, best_config, best_timing = self.check_all_tuning_directions(
                    func, best_config, best_timing
                )

                if improved:
                    msg = red_text(
                        "%s: Coordinate descend tuning found improvement of %.3fx by looking in all directions."
                    )
                    log.debug(
                        msg,
                        self.name,
                        old_best_timing / best_timing,
                    )

        log.debug(
            "%s: Improve from %s %f -> %s %f, %.3fx",
            self.name,
            baseline_config,
            baseline_timing,
            best_config,
            best_timing,
            baseline_timing / best_timing,
        )

        return best_config