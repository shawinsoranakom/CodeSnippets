def _get_estimated_runtime(self) -> float:
        """
        Returns estimated op runtime in milliseconds (ms)
        """
        buf = self.get_nodes()[0].get_outputs()[0]
        layout = buf.node.get_output_spec()
        if not is_gpu(get_device_type(layout)):
            # default to no reordering based on runtime
            return 0

        # Collective kernels
        if is_collective(self.node):
            assert isinstance(self.node, ir.IRNode)
            try:
                if config_comms.runtime_estimations_use_nccl_lib_estimations:
                    cache_key = get_estimate_runtime_cache_key_from_snode(self)
                    cache = get_estimate_runtime_cache()
                    cache_val = cache.lookup(cache_key)
                    if cache_val is not None:
                        assert isinstance(cache_val, float)
                        return cache_val

                    ms = estimate_nccl_collective_runtime_nccl_estimator(self)
                    if ms is None:
                        # NCCL estimations fail: fallback to in-tree algorithmic estimation.
                        ms = estimate_nccl_collective_runtime(self.node)

                    cache.set_value(cache_key, value=ms)
                    return ms
                return estimate_nccl_collective_runtime(self.node)
            except ValueError as e:
                # We don't know how to estimate runtime for this collective,
                # falling back to 0
                log.info(e)
                return 0
            except TypeError as e:
                # this happens when the collective is not of type ir._CollectiveKernel
                log.info(e)
                return 0

        elif is_wait(self.node):
            # ir.Wait is only used for collective ops.
            # The time needed for the collective op is already estimated and considered
            # when we are processing the collective op IR node, so ir.Wait takes 0 time
            # since it doesn't take extra time to get the result after the collective is completed.
            return 0

        ret = maybe_estimate_runtime_benchmark(self)
        if ret is not None:
            return ret

        dtype = buf.node.maybe_get_dtype()
        try:
            gpu_memory_bandwidth = get_gpu_dram_gbps()
            gpu_flops = get_device_tflops(dtype) * 10**12
            # If cudaGetDeviceProperties returns 0 for gpu_memory_bandwidth or gpu_flops
            # there is a chance to continue execution successfully. Otherwise, it would fail with
            # ZeroDivisionError below.
            if gpu_memory_bandwidth <= 0:
                raise AssertionError(
                    f"gpu_memory_bandwidth cannot be <= 0, but got {gpu_memory_bandwidth}"
                )
            if gpu_flops <= 0:
                raise AssertionError(f"gpu_flops cannot be <= 0, but got {gpu_flops}")
        except Exception:
            return 0

        flops_est = self.estimate_flops()

        if flops_est == 0 or flops_est is None:
            # no flops estimate, so fall back to memory estimate
            ns = self.get_read_write_buffers_sizes() / gpu_memory_bandwidth
            ms = ns / 1e6
            return ms

        # TODO(xmfan): find a better heuristic to model FLOPS/latency relationship
        factor = 1.0
        counted_bytes = self.get_read_write_buffers_sizes()
        counted_bytes = 0 if counted_bytes is None else counted_bytes
        compute_time = (factor * flops_est / gpu_flops) * 1e9
        transfer_time = counted_bytes / gpu_memory_bandwidth

        # Return estimated runtime in milliseconds
        ns = max(compute_time, transfer_time)
        ms = ns / 1e6
        return ms