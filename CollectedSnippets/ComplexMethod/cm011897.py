def benchmark(self, *input_tensors: torch.Tensor, out: torch.Tensor | None = None):
        if out is not None and out.numel() == 0:
            # no need to run the kernel of do benchmarking
            return 0.0
        if self.has_out_variant or len(input_tensors) == 0:
            return super().benchmark(*input_tensors, out=out)
        else:
            algo = self.to_callable()
            out_new = algo(*input_tensors)
            if out is not None:
                torch._C._dynamo.guards.assert_size_stride(
                    out_new, tuple(out.size()), tuple(out.stride())
                )
                out.copy_(out_new)  # for correctness checking
            if self.benchmark_with_cudagraphs:
                return benchmarker.benchmark_gpu_with_cuda_graph(
                    lambda: algo(*input_tensors)
                )
            if config.profile_bandwidth_with_do_bench_using_profiling:
                return do_bench_using_profiling(lambda: algo(*input_tensors))
            return benchmarker.benchmark(algo, input_tensors, {})