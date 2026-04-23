def test_two_graphs(
        self, use_background_threads, use_cuda_host_register, use_memory, delete_memory
    ):
        # Pinned host memory belongs to private pools, not to
        # graphs. Therefore, using two graphs that share a pool
        # instead of one graph does not change any of our invariants.
        with (
            caching_host_allocator_use_background_threads(use_background_threads),
            caching_host_allocator_use_host_register(use_cuda_host_register),
        ):
            shared_pool = torch.cuda.graph_pool_handle()
            graph1 = torch.cuda.CUDAGraph()
            graph2 = torch.cuda.CUDAGraph()

            with torch.cuda.graph(
                graph1, pool=shared_pool, capture_error_mode="thread_local"
            ):
                data = torch.randn(8).pin_memory()
                if use_memory:
                    data_gpu = torch.randn(8, device="cuda")
                    data_gpu.copy_(data, non_blocking=True)

                old_data_ptr = data.data_ptr()
                if delete_memory:
                    del data

            with torch.cuda.graph(
                graph2, pool=shared_pool, capture_error_mode="thread_local"
            ):
                data2 = torch.randn(8).pin_memory()
                if use_memory:
                    data_gpu = torch.randn(8, device="cuda")
                    data_gpu.copy_(data2, non_blocking=True)

                new_data_ptr = data2.data_ptr()
                if delete_memory:
                    del data2

            if delete_memory and not use_memory:
                if new_data_ptr != old_data_ptr:
                    raise AssertionError("new_data_ptr should equal old_data_ptr")
            else:
                if new_data_ptr == old_data_ptr:
                    raise AssertionError("new_data_ptr should differ from old_data_ptr")