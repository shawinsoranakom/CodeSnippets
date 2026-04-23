def test_graph_memory_stats_and_use_result_after_destroy_graph(self):
        kSmallSize = 1048576
        kSmallBuffer = 2097152
        kLargeBuffer = 20971520
        kMinLargeAlloc = 10485760
        kRoundLarge = 2097152

        elem = 4

        cases = (
            (512 // elem, 1, kSmallBuffer, kSmallBuffer, "small_pool"),
            (kSmallSize // elem, 2, 2 * kSmallBuffer, kSmallBuffer, "small_pool"),
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
        torch.xpu.empty_cache()

        s = torch.xpu.Stream()

        for (
            numel,
            delta_xpuMallocs,
            delta_xpuMalloc_bytes,
            delta_xpuMalloc_bytes_post_del_g,
            pool_string,
        ) in cases:
            if pool_string == "small_pool":
                delta_active_blocks = 3  # one from "b" plus a sneaky two from XPUGraph's one-element rng seed and offset holders
                delta_active_bytes = (
                    numel * elem + 1024
                )  # + 1024 for XPUGraph's rng seed and offset holders each
            else:
                delta_active_blocks = 1  # We only check the large pool, which isn't affected by rng offset holder
                delta_active_bytes = numel * elem

            g = torch.xpu.XPUGraph()
            s.wait_stream(torch.xpu.current_stream())
            with torch.xpu.stream(s):
                a = torch.ones((numel,), device="xpu")

                precapture_stats = torch.xpu.memory_stats()

                g.capture_begin()
                b = a.clone()
                for _ in range(5):
                    b = b.clone() + 1
                g.capture_end()
            torch.xpu.current_stream().wait_stream(s)

            gc.collect()

            postcapture_stats = torch.xpu.memory_stats()

            expecteds = (
                delta_xpuMallocs,
                delta_xpuMalloc_bytes,
                delta_active_blocks,
                delta_active_bytes,
            )
            # Double checks replay and stats before and after a call to empty_cache
            for i in range(2):
                for stat, expected in zip(stats_to_check, expecteds):
                    stat = stat + pool_string + ".current"
                    current = postcapture_stats[stat] - precapture_stats[stat]

                    if self.expandable_segments and "segment" in stat:
                        expected = 0
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
                    torch.xpu.empty_cache()

            del g
            gc.collect()
            torch.xpu.empty_cache()
            postdel_stats = torch.xpu.memory_stats()

            # Uses graph result b after graph has been deleted
            self.assertEqual(b.sum().item(), 6 * numel)

            # b should be the only live reference remaining from the graph's private pool
            expecteds = (1, delta_xpuMalloc_bytes_post_del_g, 1, numel * elem)
            for stat, expected in zip(stats_to_check, expecteds):
                stat = stat + pool_string + ".current"
                current = postdel_stats[stat] - precapture_stats[stat]

                if self.expandable_segments and "segment" in stat:
                    expected = 0
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
            torch.xpu.synchronize()
            torch.xpu.empty_cache()