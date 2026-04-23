def _print_perf_result(self, results, test_case):
        if self.args.report_aibench:
            # Output for AIBench
            # Print out per iteration execution time instead of avg time
            return
            test_name = "_".join([test_case.framework, test_case.test_config.test_name])
            for run in range(self.num_runs):
                print(
                    f"{test_case.framework}Observer "
                    + json.dumps(
                        {
                            "type": test_name,
                            "metric": "latency",
                            "unit": "us",
                            "value": str(results["reported_run_time_us"[run]]),
                        }
                    )
                )
        else:
            print(
                f"# Mode: {'JIT' if self.use_jit else 'Compile' if self.use_compile else 'Eager'}"
            )
            print(
                f"# Name: {test_case.test_config.test_name}\n# Input: {test_case.test_config.input_config}"
            )

            mode = "Backward" if test_case.test_config.run_backward else "Forward"
            if self.num_runs > 1:
                for run in range(self.num_runs):
                    print(
                        f"Run: {run}, {mode} Execution Time (us) : {results['reported_run_time_us'][run]:.3f}"
                    )
                print()
            else:
                print(
                    f"{mode} Execution Time (us) : {results['reported_run_time_us'][0]:.3f}"
                )
                print(f"Peak Memory (KB) : {results['peak_memory']}")
                # Calculate and print memory bandwidth if operator provides memory traffic
                if results.get("memory_bandwidth_gb_s") is not None:
                    print(
                        f"Memory Bandwidth (GB/s) : {results['memory_bandwidth_gb_s']:.2f}"
                    )
                print()