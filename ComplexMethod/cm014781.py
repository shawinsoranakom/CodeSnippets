def test_snapshot_include_traces(self):
        """Test that snapshot() include_traces parameter works correctly"""
        import time

        torch.cuda.empty_cache()
        torch.cuda.memory._record_memory_history()

        pool = torch.cuda.MemPool()

        # Generate trace entries
        with torch.cuda.use_mem_pool(pool):
            tensors = []
            for i in range(1000):
                tensors.append(torch.randn(1024, device="cuda"))
            del tensors

        NUM_RUNS = 10
        times_pool_full = []
        times_pool_notrace = []
        times_global_full = []
        times_global_notrace = []

        # Measure mempool snapshot without traces
        for _ in range(NUM_RUNS):
            # warmup
            snapshot = pool.snapshot(include_traces=False)
        for _ in range(NUM_RUNS):
            start = time.perf_counter()
            snapshot = pool.snapshot(include_traces=False)
            times_pool_notrace.append((time.perf_counter() - start) * 1000)

        # Measure global snapshot without traces
        for _ in range(NUM_RUNS):
            # warmup
            snapshot = torch.cuda.memory_snapshot(include_traces=False)
        for _ in range(NUM_RUNS):
            start = time.perf_counter()
            snapshot = torch.cuda.memory_snapshot(include_traces=False)
            times_global_notrace.append((time.perf_counter() - start) * 1000)

        # Measure mempool snapshot with traces
        for _ in range(NUM_RUNS):
            # warmup
            snapshot = pool.snapshot()
        for _ in range(NUM_RUNS):
            start = time.perf_counter()
            snapshot = pool.snapshot()
            times_pool_full.append((time.perf_counter() - start) * 1000)

        # Measure global snapshot with traces
        for _ in range(NUM_RUNS):
            # warmup
            snapshot = torch.cuda.memory_snapshot()
        for _ in range(NUM_RUNS):
            start = time.perf_counter()
            snapshot = torch.cuda.memory_snapshot()
            times_global_full.append((time.perf_counter() - start) * 1000)

        self.assertTrue(len(snapshot) > 0)

        print(f"Mempool with traces:    {sum(times_pool_full) / NUM_RUNS:.1f} ms")
        print(f"Mempool without traces: {sum(times_pool_notrace) / NUM_RUNS:.1f} ms")
        print(f"Global with traces:     {sum(times_global_full) / NUM_RUNS:.1f} ms")
        print(f"Global without traces:  {sum(times_global_notrace) / NUM_RUNS:.1f} ms")
        print()
        print(f"Mempool speedup: {sum(times_pool_full) / sum(times_pool_notrace):.1f}x")
        print(
            f"Global speedup: {sum(times_global_full) / sum(times_global_notrace):.1f}x"
        )

        torch.cuda.memory._record_memory_history(enabled=None)