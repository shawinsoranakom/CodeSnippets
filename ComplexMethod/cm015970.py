def test_execution_trace_start_stop(self, device):
        use_device = (
            torch.profiler.ProfilerActivity.CUDA
            or torch.profiler.ProfilerActivity.XPU in supported_activities()
            or torch.profiler.ProfilerActivity.HPU in supported_activities()
        )
        # Create a temp file to save execution trace data.
        with tempfile.NamedTemporaryFile("w+t", suffix=".et.json", delete=False) as fp:
            filename = fp.name
        expected_loop_events = 0
        et = ExecutionTraceObserver().register_callback(filename)
        for idx in range(10):
            if idx == 3:
                et.start()
            elif idx == 5:
                et.stop()
            elif idx == 8:
                et.start()
            elif idx == 9:
                et.stop()
            if et._execution_trace_running:
                expected_loop_events += 1
            with record_function(f"## LOOP {idx} ##"):
                self.payload(device, use_device=use_device)

        if filename != et.get_output_file_path():
            raise AssertionError(
                f"Expected output file path {filename}, got {et.get_output_file_path()}"
            )
        et.unregister_callback()
        nodes = self.get_execution_trace_root(filename)
        os.remove(filename)
        loop_count = 0
        found_root_node = False
        for n in nodes:
            if "name" not in n:
                raise AssertionError(f"Expected node to have 'name': {n}")
            if "[pytorch|profiler|execution_trace|process]" in n["name"]:
                found_root_node = True
            if n["name"].startswith("## LOOP "):
                loop_count += 1
        if not found_root_node:
            raise AssertionError("Expected to find root node")
        if loop_count != expected_loop_events:
            raise AssertionError(
                f"Expected {expected_loop_events} loop events, got {loop_count}"
            )