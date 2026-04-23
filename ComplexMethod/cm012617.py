def benchmark_combo_kernel(self, node_list, node_benchmark_results):
        """
        Benchmark combo kernel partitions and return total execution time.

        Generates kernel code for each partition and benchmarks them.
        Single-node partitions use benchmark_fused_nodes(), while multi-node
        partitions use the combo kernel benchmarking path.

        Returns (total_ms, total_clone_ms, file_list).
        """
        mod: ModuleType
        ms: float
        ms_clone: float

        def cache_file_path():
            assert mod.__file__ is not None
            return os.path.splitext(mod.__file__)[0] + ".kernel_perf"

        def load_cache():
            path = cache_file_path()
            if os.path.exists(path):
                with open(path) as fd:
                    return tuple(float(e) for e in fd.read().split())
            return (None, None)

        def store_cache():
            path = cache_file_path()
            write_atomic(path, str(ms) + " " + str(ms_clone))

        total_ms, file_list = 0, []
        total_clone_ms: float = 0.0
        removed_buffers_orig = V.graph.removed_buffers
        V.graph.removed_buffers = OrderedSet(removed_buffers_orig)
        inplaced_to_remove_orig = V.graph.inplaced_to_remove
        V.graph.inplaced_to_remove = OrderedSet(inplaced_to_remove_orig)
        enable_autotune = config.combo_kernels_autotune > 0
        mixed_sizes = config.combo_kernel_allow_mixed_sizes > 0
        kernel_code_list = self.generate_combo_kernel_code(
            subkernel_nodes=node_list,
            custom_part_algorithm=True,
            enable_autotune=enable_autotune,
            mixed_sizes=mixed_sizes,
            only_gen_src_code=True,
        )

        # pyrefly: ignore [bad-assignment]
        for src_code, kernel, node_group in kernel_code_list:
            fused_node_lists = [node.get_nodes() for node in node_group]
            names = [n.get_name() for nodes in fused_node_lists for n in nodes]

            if len(node_group) == 1:
                # Single-node partition: use cached benchmark results from speedup_by_combo_kernel
                node_ms, path = node_benchmark_results[node_group[0]]
                # Regular kernels have negligible clone overhead
                total_ms += node_ms
                total_clone_ms += 0
                file_list.append(path)
                continue

            assert src_code is not None
            src_code = src_code.replace(str(Placeholder.KERNEL_NAME), "triton_")
            mod = PyCodeCache.load(src_code)

            log.debug(
                "kernel src code for %s written to: %s",
                names,
                mod.__file__,
            )
            ms, ms_clone = load_cache()
            if ms is not None:
                total_ms += ms  # type: ignore[assignment]
                total_clone_ms += ms_clone
                file_list.append(mod.__file__)
                continue

            args = mod.get_args()
            call = mod.call
            wrapped_jit_function = mod.triton_

            # call once to trigger the compilation
            call(wrapped_jit_function.clone_args(*args)[0])

            launchers = wrapped_jit_function.launchers
            assert len(launchers) == 1
            if launchers[0].n_spills > 0:
                # skip benchmarking the kernel if there are register spills
                ms = ms_clone = float("inf")
            else:
                device = V.graph.get_current_device_or_throw()
                # We have to clone the inplace updated arguments to avoid earlier calls
                # generating out of range indices for later calls.
                ms = benchmarker.benchmark(
                    lambda: call(wrapped_jit_function.clone_args(*args)[0]),
                    device=device,
                )
                ms_clone = benchmarker.benchmark(
                    lambda: wrapped_jit_function.clone_args(*args)[0],
                    device=device,
                )

            log.debug(
                "The fused kernel for %s took %.3f ms to run, %.3f ms to clone inputs",
                OrderedSet(n.get_name() for n in node_group),
                ms,
                ms_clone,
            )
            store_cache()
            total_ms += ms
            total_clone_ms += ms_clone
            file_list.append(mod.__file__)
        V.graph.removed_buffers = removed_buffers_orig
        V.graph.inplaced_to_remove = inplaced_to_remove_orig
        return total_ms, total_clone_ms, file_list