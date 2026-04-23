def test_profiler_fwdbwd_flow_events_parity(self):
        """Verify that fwd->bwd flow fields on events() match Chrome trace JSON."""
        with profile(activities=[ProfilerActivity.CPU]) as prof:
            t1 = torch.ones(1, requires_grad=True)
            t2 = torch.ones(1, requires_grad=True)
            z = torch.add(t1, t2)
            y = torch.ones(1)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(z, y)
            loss.backward()

        fwdbwd_events = [
            e for e in prof.events() if e.flow_type == 1 and e.flow_id != 0
        ]
        self.assertGreater(
            len(fwdbwd_events), 0, "No fwdbwd flow events found via events()"
        )

        events_flow_starts = {e.flow_id for e in fwdbwd_events if e.flow_start}
        events_flow_ends = {e.flow_id for e in fwdbwd_events if not e.flow_start}

        with TemporaryFileName(mode="w+") as fname:
            prof.export_chrome_trace(fname)
            with open(fname) as f:
                j = json.load(f)

            json_flow_events = [
                e
                for e in j["traceEvents"]
                if e.get("ph") in ("s", "f") and e.get("cat") == "fwdbwd"
            ]
            json_flow_starts = {e["id"] for e in json_flow_events if e["ph"] == "s"}
            json_flow_ends = {e["id"] for e in json_flow_events if e["ph"] == "f"}

            self.assertEqual(
                json_flow_starts,
                events_flow_starts,
                "fwdbwd flow start IDs differ between events() and Chrome trace",
            )
            self.assertEqual(
                json_flow_ends,
                events_flow_ends,
                "fwdbwd flow end IDs differ between events() and Chrome trace",
            )