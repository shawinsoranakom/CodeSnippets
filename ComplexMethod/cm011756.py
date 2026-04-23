def speedup_by_combo_kernel(self, nodes: list[BaseSchedulerNode]) -> bool:
        """
        If config.benchmark_fusion is False, always return True.
        Otherwise, return True if fusion can brings speedup.
        """

        subkernel_nodes = nodes
        device = subkernel_nodes[0].get_device()

        assert all(node.get_device() == device for node in subkernel_nodes), (
            "All nodes in a combo kernel group must be on the same device"
        )

        if not config.benchmark_combo_kernel:
            return True

        from triton.compiler.errors import CompilationError

        ms1, path1_list = 0.0, []
        node_benchmark_results = {}
        for i, snode in enumerate(subkernel_nodes):
            node_list = snode.get_nodes()
            # We can not accurately benchmark kernel using atomic_add
            # due to how we generate random integer inputs.
            if self._any_atomic_add(node_list):
                fusion_log.debug(
                    "ComboKernel: benchmarking may not accurate due to atomic_add"
                )

            try:
                ms, path = self.benchmark_fused_nodes(node_list)
                node_benchmark_results[snode] = (ms, path)
                if math.isinf(ms):
                    fusion_log.debug(
                        "ComboKernel benchmark: register spilling of %d-th subkernel",
                        i,
                    )
                    return False
            except CompilationError as e:
                # workaround triton issue: https://github.com/triton-lang/triton/issues/2151
                if "Loop-carried variable" in str(e):
                    fusion_log.debug(
                        "ComboKernel benchmark: return True because of loop-carried variable"
                    )
                    return True  # allow fusion
                else:
                    raise
            ms1 += ms
            path1_list.append(path)

        try:
            ms2, ms2_clone, _path2_list = self.benchmark_combo_kernel(
                subkernel_nodes, node_benchmark_results
            )
        except CompilationError as e:
            # workaround triton issue: https://github.com/triton-lang/triton/issues/2151
            if "Loop-carried variable" in str(e):
                fusion_log.debug(
                    "ComboKernel benchmark: return True because of loop-carried variable"
                )
                return True  # allow fusion
            else:
                raise

        # small kernels are very likely to have speedup but hard to benchmark. So we skip benchmarking.
        small_kernel = ms2 - ms2_clone < 0.3 or ms1 < 0.3
        if fusion_log.isEnabledFor(logging.DEBUG):
            if ms1 > ms2 or small_kernel:
                fusion_log.debug(
                    "can fuse (benchmark): fusing causes %sx speedup",
                    green_text(f"{ms1 / ms2:.3f}"),
                )
            else:
                fusion_log.debug(
                    "cannot fuse (benchmark): fusing causes %sx slowdown",
                    red_text(f"{ms1 / ms2:.3f}"),
                )
        # ms1 returned by benchmark_fused_nodes discounted clone time
        return ms2 - ms2_clone < ms1 or small_kernel