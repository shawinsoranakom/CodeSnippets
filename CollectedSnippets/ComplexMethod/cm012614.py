def benchmark_codegened_module(
        self, mod, n_spills_threshold=8, node_names: OrderedSet[str] | None = None
    ) -> tuple[float, str]:
        """Benchmark an already compiled module"""
        device_interface = get_interface_for_device(V.graph.device_type)
        with (
            preserve_rng_state(),
            device_interface.device(V.graph.get_current_device_or_throw()),  # type: ignore[attr-defined]
        ):
            ms = None

            def cache_file_path():
                assert mod.__file__ is not None
                return os.path.splitext(mod.__file__)[0] + ".kernel_perf"

            def store_cache():
                path = cache_file_path()
                write_atomic(path, str(ms))

            def load_cache():
                path = cache_file_path()
                if os.path.exists(path):
                    with open(path) as fd:
                        return float(fd.read())
                return None

            node_names = (
                node_names if node_names is not None else OrderedSet(["unknown"])
            )
            log.debug(
                "kernel src code for %s written to: %s",
                node_names,
                mod.__file__,
            )
            ms = load_cache()
            if ms is not None:
                return ms, mod.__file__

            args = mod.get_args()
            call = mod.call
            wrapped_jit_function = mod.triton_
            # call once to trigger the compilation
            try:
                call(wrapped_jit_function.clone_args(*args)[0])
            except Exception as e:
                if config.triton.disallow_failing_autotune_kernels_TESTING_ONLY:
                    raise
                log.debug(
                    "Exception (%s) in compiling fused nodes %s",
                    e,
                    node_names,
                )
                ms = float("inf")
                store_cache()
                return ms, mod.__file__

            launchers = wrapped_jit_function.launchers
            assert len(launchers) == 1
            # n_spills does not necessarily mean it's not profitable to fuse,
            # and sometimes it can be inaccurate
            if launchers[0].n_spills > n_spills_threshold:
                # skip benchmarking the kernel if there are register spills
                ms = float("inf")
            else:
                device = V.graph.get_current_device_or_throw()
                # We have to clone the inplace updated arguments to avoid earlier calls
                # generating out of range indices for later calls.
                ms = benchmarker.benchmark(
                    lambda: call(wrapped_jit_function.clone_args(*args)[0]),
                    device=device,
                )
                # overhead of cloning args gives bias for fusing the kernel
                # in the case of mutating/in-placeable second fusion
                # TODO - would be better as a hook in triton do_bench that reset
                # the input values between benchmarking
                if len(wrapped_jit_function.mutated_arg_names) > 0:
                    ms = ms - benchmarker.benchmark(
                        lambda: wrapped_jit_function.clone_args(*args),
                        device=str(device),
                    )

            log.debug(
                "The fused kernel for %s took %.3f ms to run",
                node_names,
                ms,
            )
            store_cache()
            return ms, mod.__file__