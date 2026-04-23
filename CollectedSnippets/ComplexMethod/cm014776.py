def test_graph_memory_stats_and_use_result_after_destroy_graph(self):
        kSmallSize = 1048576
        kSmallBuffer = 2097152
        kLargeBuffer = 20971520
        kMinLargeAlloc = 10485760
        kRoundLarge = 2097152

        elem = 4

        # this was annoying to write but stresses the expectations pretty rigorously
        # For small_pool cases, delta_cudaMallocs and delta_cudaMalloc_bytes include
        # an extra kSmallBuffer segment for the per-capture RNG state tensors, which
        # are allocated on the default stream (separate from stream s).
        cases = (
            (512 // elem, 2, 2 * kSmallBuffer, kSmallBuffer, "small_pool"),
            (kSmallSize // elem, 3, 3 * kSmallBuffer, kSmallBuffer, "small_pool"),
            ((kSmallSize + 512) // elem, 1, kLargeBuffer, kLargeBuffer, "large_pool"),
            (
                (kMinLargeAlloc - 512) // elem,
                2,
                2 * kLargeBuffer,
                kLargeBuffer,
                "large_pool",
            ),
            (
                (kMinLargeAlloc + 512) // elem,
                3,
                3
                * (
                    kRoundLarge
                    * ((kMinLargeAlloc + 512 + kRoundLarge - 1) // kRoundLarge)
                ),
                kRoundLarge * ((kMinLargeAlloc + 512 + kRoundLarge - 1) // kRoundLarge),
                "large_pool",
            ),
        )

        stats_to_check = ("segment.", "reserved_bytes.", "active.", "active_bytes.")

        gc.collect()
        torch.cuda.empty_cache()

        s = torch.cuda.Stream()

        for (
            numel,
            delta_cudaMallocs,
            delta_cudaMalloc_bytes,
            delta_cudaMalloc_bytes_post_del_g,
            pool_string,
        ) in cases:
            if pool_string == "small_pool":
                delta_active_blocks = 3  # one from "b" plus a sneaky two from CUDAGraph's one-element rng seed and offset holders
                delta_active_bytes = (
                    numel * elem + 1024
                )  # + 1024 for CUDAGraph's rng seed and offset holders each
            else:
                delta_active_blocks = 1  # We only check the large pool, which isn't affected by rng offset holder
                delta_active_bytes = numel * elem

            g = torch.cuda.CUDAGraph()
            s.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(s):
                # Per-capture RNG state tensors are allocated on the default stream
                # (not the capture stream), so they occupy a separate segment from
                # user tensors created here on stream s.
                a = torch.ones((numel,), device="cuda")

                precapture_stats = torch.cuda.memory_stats()

                g.capture_begin()
                b = a.clone()
                for _ in range(5):
                    b = b.clone() + 1
                g.capture_end()
            torch.cuda.current_stream().wait_stream(s)

            gc.collect()

            postcapture_stats = torch.cuda.memory_stats()

            expecteds = (
                delta_cudaMallocs,
                delta_cudaMalloc_bytes,
                delta_active_blocks,
                delta_active_bytes,
            )
            # Double checks replay and stats before and after a call to empty_cache
            for i in range(2):
                for stat, expected in zip(stats_to_check, expecteds):
                    stat = stat + pool_string + ".current"
                    current = postcapture_stats[stat] - precapture_stats[stat]

                    # There will only ever be one expandable segment in each of the small and large pools. The way the
                    # bookkeeping is done in the allocator means that we never increment the number of segments.
                    if self.expandable_segments and "segment" in stat:
                        expected = 0
                    # These two cases hit an edge case where the PyTorch allocator won't immediately unmap part of an
                    # expandable segment (and as a result reduce the number of reserved bytes) if the block to unmap is
                    # smaller than the page size
                    if (
                        self.expandable_segments
                        and "reserved" in stat
                        and (numel == cases[3][0] or numel == cases[4][0])
                    ):
                        expected = 2 * kLargeBuffer

                    self.assertEqual(
                        current,
                        expected,
                        "Pre to post capture delta of "
                        + stat
                        + f" = {current}, expected = {expected}, numel = {numel}",
                    )

                g.replay()
                self.assertEqual(b.sum().item(), 6 * numel)
                if i == 0:
                    torch.cuda.empty_cache()

            del g
            gc.collect()
            torch.cuda.empty_cache()
            postdel_stats = torch.cuda.memory_stats()

            # Uses graph result b after graph has been deleted
            self.assertEqual(b.sum().item(), 6 * numel)

            # b should be the only live reference remaining from the graph's private pool
            expecteds = (1, delta_cudaMalloc_bytes_post_del_g, 1, numel * elem)
            for stat, expected in zip(stats_to_check, expecteds):
                stat = stat + pool_string + ".current"
                current = postdel_stats[stat] - precapture_stats[stat]

                # There will only ever be one expandable segment in each of the small and large pools. The way the
                # bookkeeping is done in the allocator means that we never increment the number of segments.
                if self.expandable_segments and "segment" in stat:
                    expected = 0
                # These two cases hit an edge case where the PyTorch allocator won't immediately unmap part of an
                # expandable segment (and as a result reduce the number of reserved bytes) if the block to unmap is
                # smaller than the page size
                if (
                    self.expandable_segments
                    and "reserved" in stat
                    and numel == cases[3][0]
                ):
                    expected = 2 * kLargeBuffer
                if (
                    self.expandable_segments
                    and "reserved" in stat
                    and numel == cases[4][0]
                ):
                    expected = kLargeBuffer

                self.assertEqual(
                    current,
                    expected,
                    "Pre capture to post graph delete delta of "
                    + stat
                    + f" = {current}, expected = {expected}, numel = {numel}",
                )

            # del a, b before the next case is essential, otherwise overwriting a and b in the next case
            # can throw off its allocation/deallocation counts.
            del a, b
            # Tensors used across streams (a and b) were held until just now, so no need to call record_stream on them.
            torch.cuda.synchronize()
            torch.cuda.empty_cache()