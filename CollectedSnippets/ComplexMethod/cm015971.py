def test_execution_trace_repeat_in_loop(self, device):
        use_device = (
            torch.profiler.ProfilerActivity.CUDA
            or torch.profiler.ProfilerActivity.XPU in supported_activities()
            or torch.profiler.ProfilerActivity.HPU in supported_activities()
        )
        iter_list = {3, 4, 6, 8}
        expected_loop_events = len(iter_list)
        output_files = []
        for idx in range(10):
            if idx in iter_list:
                # Create a temp file to save execution trace data.
                with tempfile.NamedTemporaryFile(
                    "w+t", suffix=".et.json", delete=False
                ) as fp:
                    output_files.append(fp.name)
                    et = ExecutionTraceObserver().register_callback(fp.name)
                et.start()
            with record_function(f"## LOOP {idx} ##"):
                self.payload(device, use_device=use_device)
            if idx in iter_list:
                et.stop()
                et.unregister_callback()

        event_count = 0
        for et_file in output_files:
            nodes = self.get_execution_trace_root(et_file)
            found_root_node = False
            for n in nodes:
                if "name" not in n:
                    raise AssertionError(f"Expected node to have 'name': {n}")
                if "[pytorch|profiler|execution_trace|process]" in n["name"]:
                    if n["id"] != 1:
                        raise AssertionError(f"Expected root node id 1, got {n['id']}")
                    found_root_node = True
                if n["name"].startswith("## LOOP "):
                    event_count += 1
            if not found_root_node:
                raise AssertionError("Expected to find root node")
        if event_count != expected_loop_events:
            raise AssertionError(
                f"Expected {expected_loop_events} loop events, got {event_count}"
            )