def get_timings(hint_override: int | None = None):
                    filtered_choices = [
                        c
                        for c in choices
                        if not hasattr(c, "hint_override")
                        or c.hint_override == hint_override
                    ]
                    timings = self.do_autotuning(
                        name,
                        input_nodes,
                        layout,
                        input_gen_fns,
                        inputs_key,
                        filtered_choices,
                        precompile_fn,
                        hint_override=hint_override,
                        best_config_future=best_config_future,
                    )
                    min_extern_choice = float("inf")
                    for choice, timing in timings.items():
                        if isinstance(choice, ExternKernelCaller):
                            min_extern_choice = min(min_extern_choice, timing)

                    timings = {
                        choice: time
                        for choice, time in timings.items()
                        if (
                            time <= min_extern_choice
                            or not isinstance(choice, ExternKernelCaller)
                        )
                    }

                    return timings