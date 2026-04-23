def get_common_patches(
        self,
        async_compile: bool,
        persistent_tma: bool,
        *,
        aten_time: float | None = None,
        triton_time: float | None = None,
        mock_n_spills: int | None = None,
        mock_fused_n_regs: int | None = None,
        mock_unfused_n_regs: int | None = None,
        epilogue_runtime: float | None = None,
    ):
        from torch._inductor.autotune_process import TritonBenchmarkRequest
        from torch._inductor.runtime.triton_heuristics import CachingAutotuner
        from torch._inductor.scheduler import BaseSchedulerNode

        common_patches = [
            config.patch(
                {
                    "triton.enable_persistent_tma_matmul": persistent_tma,
                    "compile_threads": 1
                    if not async_compile
                    else config.compile_threads,
                }
            ),
            mock.patch(
                "torch._inductor.kernel.mm.autotune_select_algorithm",
                autotune_select_algorithm_wrapper_return_multi(),
            ),
            fresh_cache(),
        ]

        if aten_time is not None and triton_time is not None:
            common_patches.extend(
                [
                    mock.patch.object(
                        AlgorithmSelectorCache,
                        "benchmark_choice",
                        mock_benchmark_choice_wrapper(aten_time, triton_time),
                    ),
                    mock.patch(
                        "torch._inductor.autotune_process.run_autotune_in_subprocess",
                        mock_benchmark_choice_wrapper(aten_time, triton_time),
                    ),
                ]
            )

        if mock_n_spills is not None or mock_fused_n_regs is not None:
            original_precompile = CachingAutotuner.precompile

            def mock_precompile(self, *args, **kwargs):
                original_precompile(self, *args, **kwargs)
                for launcher in self.launchers:
                    if mock_n_spills is not None:
                        launcher.n_spills = mock_n_spills
                    if mock_fused_n_regs is not None:
                        launcher.n_regs = mock_fused_n_regs

            common_patches.append(
                mock.patch.object(CachingAutotuner, "precompile", mock_precompile)
            )

        if mock_unfused_n_regs is not None:
            original_bmreq_precompile = TritonBenchmarkRequest.precompile

            def mock_bmreq_precompile(self):
                original_bmreq_precompile(self)
                self.n_regs = mock_unfused_n_regs

            common_patches.append(
                mock.patch.object(
                    TritonBenchmarkRequest, "precompile", mock_bmreq_precompile
                )
            )

        if epilogue_runtime is not None:
            common_patches.append(
                mock.patch.object(
                    BaseSchedulerNode,
                    "_get_estimated_runtime",
                    lambda node: epilogue_runtime,
                )
            )

        with contextlib.ExitStack() as stack:
            for p in common_patches:
                stack.enter_context(p)

            yield