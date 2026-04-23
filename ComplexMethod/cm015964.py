def test_execution_trace_with_kineto(self, device):
        trace_called_num = 0

        def trace_handler(p):
            nonlocal trace_called_num
            trace_called_num += 1

        use_device = (
            torch.profiler.ProfilerActivity.CUDA
            or torch.profiler.ProfilerActivity.XPU in supported_activities()
            or torch.profiler.ProfilerActivity.HPU in supported_activities()
        )
        # Create a temp file to save execution trace and kineto data.

        with (
            tempfile.NamedTemporaryFile("w+t", suffix=".et.json", delete=False) as fp,
            tempfile.NamedTemporaryFile(
                mode="w+t", suffix=".kineto.json", delete=False
            ) as kt,
            profile(
                activities=supported_activities(),
                schedule=torch.profiler.schedule(
                    skip_first=3, wait=1, warmup=1, active=2, repeat=1
                ),
                on_trace_ready=trace_handler,
                execution_trace_observer=(
                    ExecutionTraceObserver().register_callback(fp.name)
                ),
            ) as p,
        ):
            trace_name = fp.name
            kt_name = kt.name
            for idx in range(10):
                with record_function(f"## LOOP {idx} ##"):
                    self.payload(device, use_device=use_device)
                p.step()
            self.assertEqual(fp.name, p.execution_trace_observer.get_output_file_path())

        # Uncomment for debugging
        # print("Output kineto = ", kt.name)
        # print("Output ET = ", fp.name)

        p.export_chrome_trace(kt_name)
        self.assertEqual(trace_called_num, 1)

        nodes = self.get_execution_trace_root(trace_name)
        os.remove(trace_name)
        loop_count = 0
        found_root_node = False
        for n in nodes:
            if "name" not in n:
                raise AssertionError(f"Expected node to have 'name': {n}")
            if "[pytorch|profiler|execution_trace|process]" in n["name"]:
                found_root_node = True
            if n["name"].startswith("## LOOP "):
                loop_count += 1
        self.assertTrue(found_root_node)
        # Since profiler trace is active for 2 iterations
        self.assertEqual(loop_count, 2)

        # Compare the collected Execution Trace and Kineto Trace
        # in terms of record func ID (rf_id) and External IDs
        # both of these should match for the same trace window.

        with open(kt_name) as f:
            kineto = json.load(f)
            events = kineto["traceEvents"]
        os.remove(kt_name)

        # Look up rf_ids in both Execution and Kineto trace as two lists.
        rf_ids_et = self.get_execution_trace_rf_ids(nodes)
        rf_ids_kineto = self.get_kineto_rf_ids(events)

        self.assertCountEqual(rf_ids_et, rf_ids_kineto)
        self.assertListEqual(
            rf_ids_et,
            rf_ids_kineto,
            msg=f"ET and kineto rf_id should exactly match\n"
            f"  rf_ids_et = {rf_ids_et}\n"
            f"  rf_ids_kineto = {rf_ids_kineto}\n",
        )