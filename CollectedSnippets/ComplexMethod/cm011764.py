def benchmark_when_ready() -> bool:
                nonlocal choice_timings, future_choices, ms1, min_choice, multi_node
                min_ms_fused = float("inf")
                ms_fused_choice = None
                new_timings = {}

                if get_choice_timings_async:
                    assert multi_node and isinstance(multi_node, ir.MultiTemplateBuffer)
                    choice_timings = multi_node.choice_timings()
                    min_choice, ms1 = multi_node.get_min_choice()

                    # Some choices can fail to benchmark, inf timing
                    future_choices = [
                        fut_choice
                        for fut_choice in future_choices
                        if fut_choice[0] in choice_timings
                    ]

                    future_choices = sorted(
                        future_choices,
                        key=lambda x: choice_timings[x[0]],
                    )
                # Benchmark each choice after compilation completes
                for choice, future, mod_fused in future_choices:
                    try:
                        if future is not None:
                            res = future.result()
                        elif not bench_epilogue:
                            res = mod_fused.triton_
                            res.precompile()
                        else:
                            res = None

                    # Ideally we would more narrowly catch Exceptions here but
                    # triton  will unpredictably error with valid prologue fusions
                    except Exception as e:
                        if fusion_log.isEnabledFor(logging.DEBUG):
                            fusion_log.debug(
                                "Exception in compiling %s: %s",
                                "prologue" if not epilogue_fusion else "epilogue",
                                e,
                            )
                        continue

                    if bench_epilogue:
                        # pyrefly: ignore [missing-attribute]
                        with multi_node.swap_as_triton_caller(choice):
                            ms_fused, path = self.benchmark_codegened_module(
                                mod_fused,
                                # pyrefly: ignore [bad-argument-type]
                                device,
                            )
                            new_timings[choice] = ms_fused
                            if ms_fused < min_ms_fused:
                                min_ms_fused = ms_fused
                                ms_fused_choice = choice
                    else:
                        fusible_choice = (
                            min_choice == choice
                            or ms2 + ms1 > choice_timings[choice] + ms2_fused
                        )

                        if res and fusible_choice:
                            choice.precompile()
                            # pyrefly: ignore [missing-attribute]
                            assert res.launchers and choice.n_regs
                            # pyrefly: ignore [bad-index]
                            compiled_kernel = res.launchers[0]
                            # pyrefly: ignore [missing-attribute]
                            fused_n_regs = compiled_kernel.n_regs
                            # pyrefly: ignore [missing-attribute]
                            fused_n_spills = compiled_kernel.n_spills
                            should_fuse_epilogue = _fuse_epilogue(
                                ms1,
                                ms2,
                                choice.n_regs,
                                fused_n_regs,
                                fused_n_spills,
                                choice.bmreq.num_warps,
                                DeviceProperties.create(device),
                            )
                            if should_fuse_epilogue:
                                ms_fused_choice = choice
                                break

                if bench_epilogue:
                    log_fusion(min_ms_fused, ms1, ms2)

                if (
                    not bench_epilogue or min_ms_fused < (ms1 + ms2)
                ) and ms_fused_choice is not None:
                    if config.multi_kernel_hints:
                        hint_override_best_fusion_choice[None] = ms_fused_choice
                        # pyrefly: ignore [missing-attribute]
                        multi_node.finalize_as_triton_callers(
                            hint_override_best_fusion_choice
                        )
                    else:
                        # pyrefly: ignore [missing-attribute]
                        multi_node.finalize_as_triton_caller(ms_fused_choice)

                    if bench_epilogue:
                        # pyrefly: ignore [missing-attribute]
                        multi_node._choice_timings[None] = new_timings
                    return True
                else:
                    return False