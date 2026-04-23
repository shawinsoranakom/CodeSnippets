def speedup_by_fusion(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> FusionResult:
        """
        If config.benchmark_fusion is False, always return True.
        Otherwise, return True if fusion can brings speedup.
        """

        is_multi_template = any(
            n.is_template()
            and isinstance(n.get_template_node(), ir.MultiTemplateBuffer)
            for n in (node1, node2)
        )
        if not config.benchmark_fusion and not is_multi_template:
            return FusionResult.fuse(True)

        if (
            node1.is_template()
            and not isinstance(node1.get_template_node(), ir.TritonTemplateBuffer)
            or node1.is_foreach()
            or node2.is_foreach()
        ):
            # TODO support benchmarking epilogue fusion
            return FusionResult.fuse(True)

        node_list_1 = node1.get_nodes()
        device = node_list_1[0].get_device()
        assert device

        # don't support benchmark fusion for CPU C++ backend right now.
        if device.type == "cpu" and config.cpu_backend != "triton":
            return FusionResult.fuse(True)

        node_list_2 = node2.get_nodes()
        node_list_fused = list(itertools.chain(node_list_1, node_list_2))

        # We can not accurately benchmark kernel using atomic_add
        # due to how we generate random integer inputs.
        # Skip benchmarking them by allowing fusion.
        if self._any_atomic_add(node_list_fused):
            return FusionResult.fuse(True)

        from triton.compiler.errors import CompilationError

        why = WhyNoFuse(node1, node2)

        device = node_list_fused[0].get_device()
        assert device is not None

        def log_fusion(ms_fused: float, ms1: float, ms2: float) -> None:
            if fusion_log.isEnabledFor(logging.DEBUG):
                if ms_fused < ms1 + ms2:
                    fusion_log.debug(
                        "can fuse (benchmark): fusing %s with %s cause %sx speedup",
                        node1.get_buffer_names(),
                        node2.get_buffer_names(),
                        green_text(f"{(ms1 + ms2) / ms_fused:.3f}"),
                    )
                else:
                    fusion_log.debug(
                        "cannot fuse (benchmark): fusing %s with %s cause %sx slowdown",
                        node1.get_buffer_names(),
                        node2.get_buffer_names(),
                        red_text(f"{ms_fused / (ms1 + ms2):.3f}"),
                    )

        if is_multi_template and any(
            n.get_template_node() is not None for n in (node1, node2)
        ):
            epilogue_fusion = node1.get_template_node() is not None
            multi_node = (
                node1.get_template_node()
                if epilogue_fusion
                else node2.get_template_node()
            )
            assert isinstance(multi_node, ir.MultiTemplateBuffer)
            # Check for layout conflicts before committing to Triton template
            if self._has_layout_conflict_for_template(multi_node):
                return FusionResult.fuse(False)

            hint_override_best_fusion_choice: dict[
                int | None, TritonTemplateCallerBase
            ] = {}
            future_choices: list[tuple[Any, LambdaFuture | None, ModuleType]] = []
            for hint_override in config.multi_kernel_hints:
                choice_timings = multi_node.choice_timings(hint_override)
                for choice, _ in sorted(choice_timings.items(), key=lambda x: x[1]):
                    if not isinstance(
                        choice, torch._inductor.select_algorithm.TritonTemplateCaller
                    ):
                        continue
                    with multi_node.swap_as_triton_caller(choice):
                        future_choices.append(
                            (
                                choice,
                                *self.compile_kernel(
                                    node_list_fused, hint_override=choice.hint_override
                                ),
                            )
                        )

                min_ms_fused = float("inf")
                ms_fused_choice: TritonTemplateCallerBase | None = None
                new_timings = {}
                for choice, future, mod_fused in future_choices:
                    try:
                        if future is not None:
                            future.result()
                    except Exception as e:
                        if fusion_log.isEnabledFor(logging.DEBUG):
                            fusion_log.debug(
                                "Exception in compiling %s: %s",
                                "prologue" if not epilogue_fusion else "epilogue",
                                e,
                            )
                        continue
                    with multi_node.swap_as_triton_caller(choice):
                        ms_fused, path = self.benchmark_codegened_module(
                            mod_fused, device
                        )
                        new_timings[choice] = ms_fused
                        if ms_fused < min_ms_fused:
                            min_ms_fused = ms_fused
                            ms_fused_choice = choice
                multi_node._choice_timings[hint_override] = new_timings
                assert isinstance(ms_fused_choice, TritonTemplateCallerBase)
                hint_override_best_fusion_choice[hint_override] = ms_fused_choice

            bench_epilogue = config.benchmark_epilogue_fusion
            num_triton_callers = sum(
                isinstance(c, TritonTemplateCallerBase) for c in multi_node.choices
            )
            # Track if the choice timings can be retrieved async after compilation
            get_choice_timings_async = (
                use_pipelined_autotuning()
                and not bench_epilogue
                and num_triton_callers <= config.max_epilogue_benchmarked_choices
            )

            ms1, ms2 = float("inf"), float("inf")
            min_choice: ir.ChoiceCaller | None = None
            if not get_choice_timings_async:
                # Eagerly compile and benchmark non-template nodes
                choice_timings = multi_node.choice_timings()
                min_choice, ms1 = multi_node.get_min_choice()
                choice_timings_iter = sorted(
                    choice_timings.items(), key=operator.itemgetter(1)
                )
            else:
                # Use 0 for unfused time, won't be used as bench_epilogue
                # is guaranteed to be False here
                choice_timings_iter = [(c, 0) for c in multi_node.choices]

            if bench_epilogue:
                ms2, path2 = (
                    self.benchmark_fused_nodes(node_list_2)
                    if epilogue_fusion
                    else self.benchmark_fused_nodes(node_list_1)
                )
            else:
                # By default, don't do prologue fusion. Generally slower
                if not epilogue_fusion:
                    return FusionResult.fuse(False)

                ms2 = node2._get_estimated_runtime()
                ms2_fused = _estimate_fused_epilogue_runtime(node1, node2, ms2)

            # Start compiling choices in parallel
            from torch._inductor.codegen.simd import CantSplit

            future_choices: list[tuple[Any, LambdaFuture | None, ModuleType]] = []
            triton_choices = 0
            for choice, unfused_time in choice_timings_iter:
                if not isinstance(choice, TritonTemplateCallerBase):
                    continue

                # For prologue fusion we check if the underlying template of the choice
                # supports all allowed prologue inputs. If not, we skip this choice in
                # the fusion benchmark.
                # TODO: Remove this check after all Triton templates support prologue fusion.
                # Currently, persistent+TMA Triton template does not due to the TMA-based loads.
                if (
                    not epilogue_fusion
                    and hasattr(choice, "allowed_prologue_inps")
                    and choice.allowed_prologue_inps != multi_node.allowed_prologue_inps
                ):
                    continue

                if bench_epilogue and unfused_time >= ms1 + ms2:
                    break

                triton_choices += 1
                if triton_choices > config.max_epilogue_benchmarked_choices:
                    break

                with multi_node.swap_as_triton_caller(choice):
                    try:
                        future_choices.append(
                            (choice, *self.compile_kernel(node_list_fused))
                        )
                    except CantSplit:
                        # Epilogue node ranges may be incompatible with the
                        # template kernel's tiling groups — skip this choice.
                        continue

            if len(future_choices) == 0:
                return FusionResult.fuse(False)

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

            return FusionResult.from_callable(
                benchmark_when_ready, future_choices[0][1]
            )

        else:
            # Start parallel compilation for all three kernels
            future_and_mod_l1 = self.compile_kernel(node_list_1)
            future_and_mod_l2 = self.compile_kernel(node_list_2)
            future_and_mod_l1_fused = self.compile_kernel(node_list_fused)

            def benchmark_when_ready() -> bool:
                from torch._inductor.runtime.triton_heuristics import (
                    NoTritonConfigsError,
                )

                try:
                    # Wait for all compilations to complete
                    for fut in (
                        future_and_mod_l1[0],
                        future_and_mod_l2[0],
                        future_and_mod_l1_fused[0],
                    ):
                        if fut is not None:
                            fut.result()

                    ms1, path1 = self.benchmark_codegened_module(
                        future_and_mod_l1[1],
                        # pyrefly: ignore [bad-argument-type]
                        device,
                    )
                    if math.isinf(ms1):
                        why("register spilling of the first kernel")
                        return False

                    ms2, path2 = self.benchmark_codegened_module(
                        future_and_mod_l2[1],
                        # pyrefly: ignore [bad-argument-type]
                        device,
                    )
                    if math.isinf(ms2):
                        why("register spilling of the second kernel")
                        return False

                    ms_fused, path_fused = self.benchmark_codegened_module(
                        future_and_mod_l1_fused[1],
                        # pyrefly: ignore [bad-argument-type]
                        device,
                    )
                    if math.isinf(ms_fused):
                        why("register spilling of the fused kernel")
                        return False

                    log_fusion(ms_fused, ms1, ms2)

                    if (
                        is_metric_table_enabled("slow_fusion")
                        and ms_fused >= ms1 + ms2
                        and (path1, path2) not in self.logged_slow_fusion
                    ):
                        self.logged_slow_fusion.add((path1, path2))
                        get_metric_table("slow_fusion").add_row(
                            lambda: {
                                "kernel1_path": path1,
                                "kernel1_latency": ms1,
                                "kernel2_path": path2,
                                "kernel2_latency": ms2,
                                "fused_kernel_path": path_fused,
                                "fused_kernel_latency": ms_fused,
                                "slow_down_ratio": ms_fused / (ms1 + ms2),
                            }
                        )

                    return ms_fused < ms1 + ms2

                except NoTritonConfigsError:
                    return False

                except CompilationError as e:
                    if "Loop-carried variable" in str(e):
                        return True
                    raise

            return FusionResult.from_callable(
                callable_fn=benchmark_when_ready, future=future_and_mod_l1_fused[0]
            )