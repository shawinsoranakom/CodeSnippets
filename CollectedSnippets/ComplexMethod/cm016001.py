def test_profiler_activity_type_parity(self):
        """Verify activity_type on events() matches Chrome trace cat field."""
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
            x = torch.randn(32, 32, device="cuda")
            torch.mm(x, x)

        events = prof.events()
        for e in events:
            self.assertIsInstance(e.activity_type, str)
            self.assertGreater(len(e.activity_type), 0)

        mm_event = next((e for e in events if e.name == "aten::mm"), None)
        self.assertIsNotNone(mm_event)
        self.assertEqual(mm_event.activity_type, "cpu_op")

        with TemporaryFileName(mode="w+") as fname:
            prof.export_chrome_trace(fname)
            with open(fname) as f:
                j = json.load(f)

            json_name_cats = {
                (e["name"], e["cat"])
                for e in j["traceEvents"]
                if e.get("ph") == "X" and "cat" in e
            }
            for e in events:
                self.assertIn(
                    (e.name, e.activity_type),
                    json_name_cats,
                    f"activity_type mismatch for {e.name}",
                )