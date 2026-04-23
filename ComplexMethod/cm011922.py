def __call__(
        self,
        name,
        choices: list[ChoiceCaller],
        input_nodes,
        layout,
        # optional dict mapping arg indices to the functions
        # generating a torch.Tensor for that input from the
        # corresponding ir.Buffer. if passed for a given
        # arg, the function will be called instead of
        # generating a random torch.Tensor for benchmarking.
        input_gen_fns: dict[int, Callable[[ir.Buffer], torch.Tensor]] | None = None,
        precompilation_timeout_seconds: int = 60 * 60,
        return_multi_template=False,
        best_config_future=None,
        is_collective=False,
        min_speedup_threshold: float = 1.0,  # Only pick non-fallback if faster by this ratio
        benchmark_with_cudagraphs: bool = False,  # Use CUDA graphs for ExternKernelCaller benchmarking
    ):
        from .codegen.cutlass.kernel import CUTLASSTemplateCaller

        # Run preprocessing functions on choices
        for preprocessing_fn in self.preprocessing_fns:
            choices = preprocessing_fn(choices)

        # Apply benchmark_with_cudagraphs to all choices
        if benchmark_with_cudagraphs:
            for choice in choices:
                choice._benchmark_with_cudagraphs = True

        # Templates selected with input_gen_fns require specific input data to avoid IMA
        # Passing custom input gen fns to benchmark_fusion NYI, so skip deferred template selection
        # TODO(jgong5): support multi-template on CPU C++ backend
        if input_gen_fns is not None or (
            layout.device.type == "cpu" and config.cpu_backend != "triton"
        ):
            return_multi_template = False

        # TODO - assert that we have not mutating kernels here

        if len(choices) == 0:
            raise self.create_no_valid_choices(name, "No choices exist for backend.")
        log.debug("Max autotune selects from %s choices.", len(choices))

        if len(choices) == 1:
            if not isinstance(choices[0], CUTLASSTemplateCaller):
                # CUTLASSTemplateCaller still needs to go through the autotuning process to retrieve workspace size.
                node = choices[0].output_node()
                return node, choices[0]

        if config.deterministic:
            choice = self.pick_deterministic_choice(choices)
            node = choice.output_node()
            return node, choice

        inputs_key = create_inputs_key(input_nodes)

        has_cutlass = any(isinstance(c, CUTLASSTemplateCaller) for c in choices)
        if config.autotune_in_subproc or has_cutlass:
            # Warmup the subprocess pool early so it's ready for benchmarking
            torch._inductor.autotune_process.get_tuning_process_pool()

        precompile_fn = self.make_precompile_fn(
            choices,
            name,
            inputs_key,
            precompilation_timeout_seconds=precompilation_timeout_seconds,
        )

        if return_multi_template and (config.max_autotune or config.max_autotune_gemm):
            if use_pipelined_autotuning():
                assert not config.benchmark_epilogue_fusion, (
                    "Benchmarking epilogues will cause gpu contention with pipelined autotuning"
                )
                extern_kernels = [
                    c for c in choices if AlgorithmSelectorCache._is_extern(c)
                ]
                # Make sure the autotune subprocess for benchmarking is fed as much as possible
                # Extern kernels do not have to precompile, so can feed them before triton
                AsyncAutotuner.start(extern_kernels, inputs_key)
                triton_kernels = [
                    c for c in choices if not AlgorithmSelectorCache._is_extern(c)
                ]

                if triton_kernels:
                    precompile_instance = PrecompileThreadPool.get_instance()
                    precompile_future = precompile_instance.submit(
                        self.do_autotuning,
                        name,
                        input_nodes,
                        layout,
                        input_gen_fns,
                        inputs_key,
                        triton_kernels,
                        precompile_fn,
                    )
                else:
                    precompile_future = None

                def get_timings(hint_override: int | None = None):
                    assert not hint_override, (
                        "Hint not supported with pipelined autotuning"
                    )
                    # Await precompilation future, thread pool
                    precompile_start_ts = time.time()
                    final_choices = choices
                    if precompile_future:
                        try:
                            precompile_future.result()
                        except NoValidChoicesError:
                            log.error(
                                "Runtime error for autotuning triton choices, defaulting to extern kernels.",
                            )
                            final_choices = extern_kernels
                    precompile_elapse = time.time() - precompile_start_ts

                    # Await autotuning in subproc pool
                    autotune_start_ts = time.time()
                    results = AsyncAutotuner.get_results(final_choices, inputs_key)
                    autotune_wait_ts = time.time() - autotune_start_ts
                    AlgorithmSelectorCache.log_results(
                        name,
                        input_nodes,
                        results,
                        precompile_elapse,
                        autotune_wait_ts,
                    )

                    return results
            else:

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

            # We take the union of allowed prologue inputs from all choices,
            # and, within benchmark fusion, don't allow prologue fusion for
            # choices which don't support the whole union.
            allowed_prologue_inps: OrderedSet[str] = OrderedSet()
            for c in choices:
                if isinstance(c, TritonTemplateCaller):
                    allowed_prologue_inps |= c.allowed_prologue_inps

            # No single winning choice yet; selection is deferred to benchmark fusion
            return (
                torch._inductor.ir.TensorBox.create(
                    torch._inductor.ir.MultiTemplateBuffer(
                        layout,
                        input_nodes,
                        get_timings,
                        choices,
                        allowed_prologue_inps,
                    )
                ),
                None,
            )

        timings = self.do_autotuning(
            name,
            input_nodes,
            layout,
            input_gen_fns,
            inputs_key,
            choices,
            precompile_fn,
            best_config_future=best_config_future,
            is_collective=is_collective,
        )
        # if timings is empty, we really have no choice but to return a semi-random
        # choice. returning the first `ExternKernelCaller` is probably the safest bet
        # in this case, since it will generally be the ATen kernel. if there are no
        # `ExternKernelCaller`s to return, then returning the 0th kernel is our next
        # best option (ideally we'd fail whenever there is no ATen kernel to fallback
        # to, but that's not trivial to figure out)
        if timings == {}:
            for choice in choices:
                if isinstance(choice, ExternKernelCaller):
                    node = choice.output_node()
                    log.debug(
                        "Autotuning returned empty timings, falling back to first `ExternKernelCaller`: %s",
                        node,
                    )
                    return node, choice
            node = choices[0].output_node()
            choice = choices[0]
            log.debug(
                "Autotuning returned empty timings, falling back to first choice: %s",
                node,
            )
            return node, choice

        # if we got any timings at all, pick the best of those
        best_choice = min(timings, key=timings.__getitem__)
        best_time = timings[best_choice]

        # All benchmarks failed; fall back to ATen if available (#171094)
        if math.isinf(best_time):
            extern_choices = [c for c in choices if isinstance(c, ExternKernelCaller)]
            if extern_choices:
                best_choice = extern_choices[0]
                log.warning(
                    "All autotuning benchmarks failed (timing=inf). Falling back to ExternKernelCaller: %s",
                    getattr(best_choice, "name", "<unknown>"),
                )
            else:
                log.warning(
                    "All autotuning benchmarks failed (timing=inf) and no ExternKernelCaller fallback available. "
                    "Selected kernel %s may cause runtime errors.",
                    getattr(best_choice, "name", "<unknown>"),
                )

        # Apply min_speedup_threshold: only pick non-fallback if it beats fallback by threshold
        elif min_speedup_threshold > 1.0:

            def is_fallback(c: ChoiceCaller) -> bool:
                return isinstance(c, ExternKernelCaller) and getattr(
                    c.choice, "use_fallback_kernel", False
                )

            fallback_choices = [c for c in timings if is_fallback(c)]
            if fallback_choices and not is_fallback(best_choice):
                fallback_time = min(timings[c] for c in fallback_choices)
                speedup = fallback_time / best_time if best_time > 0 else 0

                if speedup < min_speedup_threshold:
                    # Best choice doesn't beat fallback by enough, use fallback instead
                    log.debug(
                        "Best choice %s speedup %.2fx < threshold %.2fx, using fallback",
                        best_choice.name,
                        speedup,
                        min_speedup_threshold,
                    )
                    best_choice = min(fallback_choices, key=lambda c: timings[c])

        best_choice = V.choices.override_best_choice(best_choice, timings)

        # Test-only: force choosing decomposition (non-fallback) if available
        if config.test_configs.force_custom_op_decomposition:

            def is_fallback(c: ChoiceCaller) -> bool:
                return isinstance(c, ExternKernelCaller) and getattr(
                    c.choice, "use_fallback_kernel", False
                )

            non_fallback_choices = [c for c in timings if not is_fallback(c)]
            if non_fallback_choices:
                best_choice = min(non_fallback_choices, key=lambda c: timings[c])

        choice = best_choice
        node = choice.output_node()

        log.debug("Autotuning selected choice: %s", node)
        return node, choice