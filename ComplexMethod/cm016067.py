def run(self):
        self._print_header()
        output_csv_filename = self.args.output_csv
        headers = [
            "Benchmarking Framework",
            "Benchmarking Module Name",
            "Case Name",
            "tag",
            "run_backward",
            "Execution Time",
            "Peak Memory (KB)",
            "Memory Bandwidth (GB/s)",
        ]

        if self.args.output_json or self.args.output_json_for_dashboard:
            perf_list = []

        for test_metainfo in BENCHMARK_TESTER:
            for test in _build_test(*test_metainfo):
                full_test_id, test_case = test
                op_test_config = test_case.test_config

                if self._print_test_case_info(test_case):
                    continue

                if not self._keep_test(test_case):
                    continue

                # To reduce variance, fix a numpy randseed to the test case,
                # so that the randomly generated input tensors remain the
                # same for each test case.
                # The random seed is limited to 32-bit because of numpy
                # requirement.
                np.random.seed(seed=hash(full_test_id) & ((1 << 32) - 1))

                print(
                    f"# Benchmarking {test_case.framework}: {test_case.op_bench.module_name()}"
                )

                if op_test_config.run_backward:
                    launch_func = self._launch_backward
                else:
                    launch_func = self._launch_forward

                # Warmup
                launch_func(
                    test_case, self.args.warmup_iterations, print_per_iter=False
                )
                # Actual Execution
                results = [
                    self._measure_metrics(
                        launch_func, test_case, self.iters, self.print_per_iter
                    )
                    for _ in range(self.num_runs)
                ]
                result_dict = dict()
                result_dict["reported_run_time_us"] = [r[0] for r in results]
                result_dict["peak_memory"] = results[0][1]

                # Calculate memory bandwidth if operator provides memory traffic
                memory_traffic_bytes = test_case.op_bench.get_memory_traffic_bytes()
                if memory_traffic_bytes is not None:
                    execution_time_s = result_dict["reported_run_time_us"][0] / 1e6
                    result_dict["memory_bandwidth_gb_s"] = (
                        memory_traffic_bytes / execution_time_s / 1e9
                    )
                else:
                    result_dict["memory_bandwidth_gb_s"] = None

                self._print_perf_result(results=result_dict, test_case=test_case)

                # output results to csv
                self._output_csv(
                    output_csv_filename,
                    headers,
                    [
                        test_case.framework,
                        test_case.op_bench.module_name(),
                        (
                            test_case.test_config.test_name + "_BACKWARD"
                            if test_case.test_config.run_backward is True
                            else test_case.test_config.test_name
                        ),
                        test_case.test_config.tag,
                        test_case.test_config.run_backward,
                        result_dict["reported_run_time_us"][0],
                        result_dict["peak_memory"],
                        result_dict["memory_bandwidth_gb_s"],
                    ],
                )
                if self.args.output_json or self.args.output_json_for_dashboard:
                    perf_list.append(self._perf_result_to_dict(result_dict, test_case))

        if self.args.output_json_for_dashboard:
            self._output_json(
                perf_list, self.args.output_json_for_dashboard, self.args.benchmark_name
            )

        if self.args.output_json:
            with open(self.args.output_json, "w") as f:
                json.dump(perf_list, f)