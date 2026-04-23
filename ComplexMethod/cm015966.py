def test_execution_trace_alone(self, device):
        use_device = (
            torch.profiler.ProfilerActivity.CUDA
            or torch.profiler.ProfilerActivity.HPU in supported_activities()
            or torch.profiler.ProfilerActivity.XPU in supported_activities()
        )
        # Create a temp file to save execution trace data.
        # Use a gzip file to test compression codepath
        with tempfile.NamedTemporaryFile("w", suffix=".et.json.gz", delete=False) as fp:
            filename = fp.name
        expected_loop_events = 0

        et = ExecutionTraceObserver().register_callback(filename)

        et.start()
        for idx in range(5):
            expected_loop_events += 1
            with record_function(f"## LOOP {idx} ##"):
                self.payload(device, use_device=use_device)
        et.stop()

        if filename != et.get_output_file_path():
            raise AssertionError(
                f"Expected output file path {filename}, got {et.get_output_file_path()}"
            )
        et.unregister_callback()
        nodes = self.get_execution_trace_root(filename)
        os.remove(filename)
        loop_count = 0
        # Expected tensor object tuple size, in th form of:
        # [tensor_id, storage_id, offset, numel, itemsize, device_str]
        tensor_tuple_size = 6
        found_root_node = False
        for n in nodes:
            if "name" not in n:
                raise AssertionError(f"Expected node to have 'name': {n}")
            if "[pytorch|profiler|execution_trace|process]" in n["name"]:
                found_root_node = True
            if n["name"].startswith("## LOOP "):
                loop_count += 1
            # Check if tensor tuple representation size is correct.
            if n["name"] == "## TEST 2 ##":
                if len(n["inputs"]["values"][3][0]) != tensor_tuple_size:
                    raise AssertionError(
                        f"Expected tensor tuple size {tensor_tuple_size}, got "
                        f"{len(n['inputs']['values'][3][0])}"
                    )
        if not found_root_node:
            raise AssertionError("Expected to find root node")
        if loop_count != expected_loop_events:
            raise AssertionError(
                f"Expected {expected_loop_events} loop events, got {loop_count}"
            )