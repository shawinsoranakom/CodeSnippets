def test_fx_memory_profiler_augmentation(self):
        """Test that memory snapshots are augmented with FX debug information."""

        class MLPModule(torch.nn.Module):
            def __init__(self):
                super().__init__()
                torch.manual_seed(5)
                self.net1 = torch.nn.Linear(10, 16, bias=True, device="xpu")
                self.relu = torch.nn.ReLU()
                self.net2 = torch.nn.Linear(16, 10, bias=True, device="xpu")

            def forward(self, x):
                a = self.net1(x)
                b = self.relu(a)
                c = self.net2(b)
                return c

        class MLPModule2(torch.nn.Module):
            def __init__(self):
                super().__init__()
                torch.manual_seed(5)
                self.net1 = torch.nn.Linear(10, 16, bias=True, device="xpu")
                self.relu = torch.nn.ReLU()
                self.net2 = torch.nn.Linear(16, 10, bias=True, device="xpu")

            def forward(self, x):
                d = self.net1(x)
                e = self.relu(d)
                f = self.net2(e)
                return f

        if self.expandable_segments:
            self.skipTest(
                "Requires driver update to fix oneDNN primitive operations when using expandable segments."
            )
        mod = MLPModule()
        gc.collect()
        torch.xpu.memory.empty_cache()
        torch.xpu.memory._record_memory_history()
        compiled = torch.compile(mod, backend="aot_eager", fullgraph=True)
        _ = compiled(torch.randn(10, 10, device="xpu"))
        augmented_snapshot = torch.xpu.memory._snapshot(augment_with_fx_traces=True)
        torch.xpu.memory._record_memory_history(enabled=None, clear_history=True)
        gc.collect()
        torch.xpu.empty_cache()

        fx_frames = self.collect_frames(augmented_snapshot)
        self.assertGreater(len(fx_frames), 2)

        for frame in fx_frames:
            # Every FX frame should have both node_op and node_name
            self.assertIn("fx_node_op", frame)
            self.assertIn("fx_node_name", frame)
            self.assertIn("fx_node_target", frame)
            self.assertIn("fx_original_trace", frame)

            self.assertIn(frame["fx_node_name"], ["addmm", "relu", "addmm_1"])
            fx_node_name = frame["fx_node_name"]
            if fx_node_name == "addmm":
                self.assertIn("a = self.net1(x)", frame["fx_original_trace"])
            elif fx_node_name == "addmm_1":
                self.assertIn("c = self.net2(b)", frame["fx_original_trace"])
            elif fx_node_name == "relu":
                self.assertIn("b = self.relu(a)", frame["fx_original_trace"])

        # Test that when we have two graphs with the same src_code, they're not hashed
        # to the same metadata
        mod = MLPModule2()
        torch.xpu.memory._record_memory_history()
        compiled = torch.compile(mod, backend="aot_eager", fullgraph=True)
        _ = compiled(torch.randn(10, 10, device="xpu"))
        augmented_snapshot = torch.xpu.memory._snapshot(augment_with_fx_traces=True)
        torch.xpu.memory._record_memory_history(enabled=None, clear_history=True)

        # avoid collecting segments from previous run for unit test purpose
        fx_frames = self.collect_frames(augmented_snapshot, collect_segments=False)
        self.assertGreater(len(fx_frames), 0)

        for frame in fx_frames:
            # Every FX frame should have both node_op and node_name
            self.assertIn("fx_node_op", frame)
            self.assertIn("fx_node_name", frame)
            self.assertIn("fx_node_target", frame)
            self.assertIn("fx_original_trace", frame)

            self.assertIn(frame["fx_node_name"], ["addmm", "relu", "addmm_1"])
            fx_node_name = frame["fx_node_name"]
            if fx_node_name == "addmm":
                self.assertIn("d = self.net1(x)", frame["fx_original_trace"])
            elif fx_node_name == "addmm_1":
                self.assertIn("f = self.net2(e)", frame["fx_original_trace"])
            elif fx_node_name == "relu":
                self.assertIn("e = self.relu(d)", frame["fx_original_trace"])