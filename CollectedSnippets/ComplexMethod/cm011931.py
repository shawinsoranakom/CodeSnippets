def log_results(
        name: str,
        input_nodes: list[ir.IRNode],
        timings: dict[ChoiceCaller, float],
        elapse: float,
        precompile_elapse: float,
        prescreening_elapse: float | None = None,
        hint_override: int | None = None,
        is_collective: bool = False,
    ):
        """Log the autotuning results, currently only handles mm and flex. Log Collective op autotuning result"""
        if is_collective and timings:
            import torch.distributed as dist

            # Only rank 0 logs to avoid duplicate logs
            rank = dist.get_rank() if dist.is_initialized() else 0
            if rank == 0:
                best_choice = min(timings, key=timings.__getitem__)
                log.warning("[COLLECTIVE AUTOTUNING] All timings:")
                for c, t in sorted(timings.items(), key=lambda x: x[1]):
                    choice_name = getattr(c, "name", str(c))
                    log.warning(
                        "  - %s: %.6f ms %s",
                        choice_name,
                        t if math.isfinite(t) else float("inf"),
                        "← SELECTED" if c == best_choice else "",
                    )

        V.debug.log_autotuning_results(
            name, input_nodes, timings, elapse, precompile_elapse
        )
        if not (config.max_autotune or config.max_autotune_gemm) or not PRINT_AUTOTUNE:
            return

        sizes = ", ".join(
            [
                "x".join(
                    map(
                        str,
                        V.graph.sizevars.optimization_hints_with_override(
                            n.get_size(),
                            hint_override=hint_override,
                        ),
                    )
                )
                for n in input_nodes
            ]
        )

        strides = ", ".join(
            [str(get_strides_with_layout_constraints(n)) for n in input_nodes]
        )
        dtypes = ", ".join([str(n.get_dtype()) for n in input_nodes])
        if config.autotune_num_choices_displayed == 0:
            return

        # when autotune_num_choices_displayed is None, [:None] means all
        n = config.autotune_num_choices_displayed
        top_k = sorted(timings, key=timings.__getitem__)[:n]

        best = top_k[0]

        # Log autotuning results for each operation type
        AlgorithmSelectorCache.maybe_log_mm_results(name, input_nodes, timings)
        AlgorithmSelectorCache.maybe_log_conv_results(name, input_nodes, timings)
        AlgorithmSelectorCache.maybe_log_flex_attention_results(
            name, input_nodes, timings
        )

        best_time = timings[best]
        sys.stderr.write(f"AUTOTUNE {name}({sizes})\n")
        sys.stderr.write(f"strides: {strides}\n")
        sys.stderr.write(f"dtypes: {dtypes}\n")

        for choice in top_k:
            result = timings[choice]
            if result:
                kernel_description = choice.description
                sys.stderr.write(
                    f"  {choice.name} {result:.4f} ms {best_time / result:.1%} {kernel_description}\n"
                )
            else:
                sys.stderr.write(
                    f"  {choice.name} {result:.4f} ms <DIVIDED BY ZERO ERROR>\n"
                )

        autotune_type_str = (
            "SubProcess" if config.autotune_in_subproc else "SingleProcess"
        )
        prescreening_msg = (
            f" and {prescreening_elapse:.4f} seconds prescreening"
            if prescreening_elapse is not None
            else ""
        )
        sys.stderr.write(
            f"{autotune_type_str} AUTOTUNE benchmarking takes {elapse:.4f} seconds and {precompile_elapse:.4f}"
            f" seconds precompiling for {len(timings)} choices"
            + prescreening_msg
            + "\n"
        )