def _measure_metrics(self, launch_test, test_case, iters, print_per_iter):
        """
        This function execute the operator for <iters> iterations then look at the time.
        If it's not significant, the number of iterations will be increased before rerun.
        The execution stops when the time becomes significant.
        """
        curr_test_total_time = 0
        time_trace = []
        peak_memory = 0
        input_values = test_case.op_bench.inputs.values()
        device, device_module = None, None
        if input_values and isinstance(next(iter(input_values)), torch.Tensor):
            # The device and device module information are crucial for memory metric calculation,
            # In case of ops where inputs are integers (not tensor), memory metrics need not be calculated.
            sample_input = next(iter(input_values))
            device = sample_input.device
            device_module = torch.get_device_module(device.type)
        # TODO: add support for cpu memory measurement
        while True:
            if hasattr(device_module, "reset_peak_memory_stats"):
                device_module.reset_peak_memory_stats(device)
            run_time_sec = launch_test(test_case, iters, print_per_iter)
            if hasattr(device_module, "synchronize"):
                device_module.synchronize(device)
            # Memory measurement process
            if hasattr(device_module, "max_memory_allocated"):
                peak_memory = device_module.max_memory_allocated(device)
            curr_test_total_time += run_time_sec
            # Analyze time after each run to decide if the result is stable
            results_are_significant = self._iteration_result_is_significant(
                iters,
                run_time_sec,
                curr_test_total_time,
                self.has_explicit_iteration_count,
            )

            report_run_time = 1e6 * run_time_sec / iters
            time_trace.append(report_run_time)
            # Print out the time spent in each epoch in ms
            if self.args.report_aibench:
                mode = (
                    "JIT"
                    if self.use_jit
                    else "Compile"
                    if self.use_compile
                    else "Eager"
                )
                test_name = "_".join(
                    [test_case.framework, test_case.test_config.test_name, mode]
                )
                print(
                    "PyTorchObserver "
                    + json.dumps(
                        {
                            "type": test_name,
                            "metric": "latency",
                            "unit": "ms",
                            "value": str(report_run_time / 1e3),
                        },
                    )
                )
            if results_are_significant:
                break

            # Re-estimate the hopefully-sufficient
            # iteration count, and run the benchmark again...
            iters = self._predict_num_iter_needed(iters)
        reported_run_time_us = np.percentile(np.array(time_trace), 50)
        return reported_run_time_us, peak_memory / 1024