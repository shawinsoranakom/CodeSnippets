def benchmark(
        self,
        *input_tensors: torch.Tensor,
        out: torch.Tensor | None = None,
    ) -> float:
        debug = autotuning_log.isEnabledFor(logging.DEBUG)
        if debug:
            start_ts = time.time()

        # create args and out tensor
        if out is None:
            assert self.input_tensor_meta and self.output_tensor_meta, (
                "Input and output tensor meta must be populated when input_tensors is empty"
            )
            assert len(input_tensors) == 0
            input_tensors = tuple(x.to_tensor() for x in self.input_tensor_meta)
            out = self.output_tensor_meta.to_tensor()

        if debug:
            create_tensor_elapse = time.time() - start_ts  # type: ignore[possibly-undefined]
            start_ts = time.time()
        try:
            fn = self.make_run_fn(*input_tensors, out=out)
        except NonzeroWorkspaceNotSupportedError:
            # Skipping all ops with nonzero workspace requirements
            autotuning_log.info("Skipping op due to nonzero workspace requirement")
            return float("inf")

        if debug:
            load_elapse = time.time() - start_ts  # type: ignore[possibly-undefined]
            start_ts = time.time()

        if self.benchmark_with_cudagraphs:
            res = benchmarker.benchmark_gpu_with_cuda_graph(fn)
        else:
            res = self.do_bench(fn, *input_tensors, out)

        if debug:
            bench_elapse = time.time() - start_ts  # type: ignore[possibly-undefined]
            autotuning_log.debug(
                "InChildProcess %s: load %f, create tensor %f, bench %f",
                self,
                load_elapse,  # type: ignore[possibly-undefined]
                create_tensor_elapse,  # type: ignore[possibly-undefined]
                bench_elapse,
            )
        self.cleanup_run_fn()
        return res