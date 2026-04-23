def test_profiler_flow_events_parity(self):
        """Verify that async CPU->GPU flow fields on events() match Chrome trace JSON."""
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
            x = torch.randn(32, 32, device="cuda")
            torch.mm(x, x)

        # Collect async CPU->GPU flow info from events()
        events_with_flow = [
            e for e in prof.events() if e.flow_id is not None and e.flow_id != 0
        ]
        self.assertGreater(
            len(events_with_flow), 0, "No flow events found via events()"
        )

        for e in events_with_flow:
            self.assertIsInstance(e.flow_id, int)
            self.assertIsInstance(e.flow_type, int)
            self.assertIsInstance(e.flow_start, bool)

        # Verify parity with Chrome trace JSON for async CPU->GPU flow
        with TemporaryFileName(mode="w+") as fname:
            prof.export_chrome_trace(fname)
            with open(fname) as f:
                j = json.load(f)

            json_flow_events = [
                e
                for e in j["traceEvents"]
                if e.get("ph") in ("s", "f") and e.get("cat") == "ac2g"
            ]
            json_flow_starts = {e["id"] for e in json_flow_events if e["ph"] == "s"}
            json_flow_ends = {e["id"] for e in json_flow_events if e["ph"] == "f"}

            # kLinkAsyncCpuGpu = 2
            ac2g_events = [e for e in events_with_flow if e.flow_type == 2]
            events_flow_starts = {e.flow_id for e in ac2g_events if e.flow_start}
            events_flow_ends = {e.flow_id for e in ac2g_events if not e.flow_start}

            self.assertEqual(
                json_flow_starts,
                events_flow_starts,
                "Async CPU->GPU flow start IDs differ between events() and Chrome trace",
            )
            self.assertEqual(
                json_flow_ends,
                events_flow_ends,
                "Async CPU->GPU flow end IDs differ between events() and Chrome trace",
            )