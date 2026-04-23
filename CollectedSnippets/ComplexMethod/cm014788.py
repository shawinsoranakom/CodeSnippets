def test_fx_memory_profiler_augmentation(self):
        """Test that memory snapshots are augmented with FX debug information."""

        device = "cuda"
        mod = self.MLPModule(device)
        # reset cache to start fresh
        torch.cuda.memory.empty_cache()
        torch.cuda.memory._record_memory_history()
        compiled = torch.compile(mod, backend="aot_eager", fullgraph=True)
        result = compiled(torch.randn(10, 10, device=device))
        augmented_snapshot = torch.cuda.memory._snapshot(augment_with_fx_traces=True)
        torch.cuda.memory._record_memory_history(enabled=None, clear_history=True)
        torch.cuda.empty_cache()

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
        mod = self.MLPModule2(device)
        torch.cuda.memory._record_memory_history()
        compiled = torch.compile(mod, backend="aot_eager", fullgraph=True)
        result = compiled(torch.randn(10, 10, device=device))
        augmented_snapshot = torch.cuda.memory._snapshot(augment_with_fx_traces=True)
        torch.cuda.memory._record_memory_history(enabled=None, clear_history=True)

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