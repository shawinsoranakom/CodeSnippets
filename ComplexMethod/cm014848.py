def test_graph_two_successive(self):
        torch.xpu.empty_cache()

        size = 1000
        kSmallBuffer = 2097152

        def func_with_temps(t, val):
            x = t.clone() + val
            y = t.clone() + val
            return x + y

        s = torch.xpu.Stream()

        for share_mem in ("Don't share", "via pool()", "via graph_pool_handle()"):
            g0 = torch.xpu.XPUGraph()
            g1 = torch.xpu.XPUGraph()

            a = torch.ones((size,), device="xpu")

            s.wait_stream(torch.xpu.current_stream())
            with torch.xpu.stream(s):
                g0_args = (
                    (torch.xpu.graph_pool_handle(),)
                    if share_mem == "via graph_pool_handle()"
                    else ()
                )
                g0.capture_begin(*g0_args)
                b = a.clone()
                for _ in range(5):
                    b = func_with_temps(b, 1)
                g0.capture_end()

                g1_args = (g0.pool(),) if share_mem == "via pool()" else g0_args
                g1.capture_begin(*g1_args)
                for _ in range(5):
                    b = func_with_temps(b, 1)
                g1.capture_end()
            torch.xpu.current_stream().wait_stream(s)

            # mixes unrelated eager ops with replays
            c = a.clone()
            for _ in range(2):
                c = func_with_temps(c, 3)
            g0.replay()
            for _ in range(2):
                c = func_with_temps(c, 3)
            g1.replay()
            for _ in range(2):
                c = func_with_temps(c, 3)

            self.assertEqual(b.sum().item(), size * 3070)
            self.assertEqual(c.sum().item(), size * 442)

            if share_mem != "Don't share":
                self.assertEqual(
                    reserved_no_sharing  # noqa: F821
                    - torch.xpu.memory_stats()["reserved_bytes.all.current"],
                    kSmallBuffer,
                )
            else:
                reserved_no_sharing = torch.xpu.memory_stats()[
                    "reserved_bytes.all.current"
                ]

            del a, b, c, g0, g1
            # Tensors used across streams (a and b) were held until just now, so no need to call record_stream on them.
            torch.xpu.synchronize()
            torch.xpu.empty_cache()