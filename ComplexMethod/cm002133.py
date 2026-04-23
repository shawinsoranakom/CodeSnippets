def run_benchmarks(
        self,
        model_id: str,
        benchmark_configs: list[BenchmarkConfig],
        num_tokens_to_profile: int = 0,
        pretty_print_summary: bool = True,
        summarized: bool = True,
    ) -> tuple[str, dict[str, Any]]:
        """Run multiple benchmarks for the given model ID and list of benchmark configs."""
        all_results = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = time.perf_counter()

        n_configs = len(benchmark_configs)
        for i, config in enumerate(benchmark_configs):
            # Skip if already run
            if config.hash in all_results:
                self.logger.info(f"Skipping duplicate config {config.name} for model {model_id} ({i + 1}/{n_configs})")
                continue

            # Otherwise, run the benchmark
            self.setup_benchmark(model_id, config)
            self.logger.info(
                f"Running benchmark of model {model_id} with scenario: {config.name} ({i + 1}/{n_configs})"
            )

            # Launch benchmark in a try/except block to avoid stopping the whole run if one benchmark fails
            try:
                result = self.run_benchmark(config, num_tokens_to_profile)
            except Exception as e:
                self.logger.error(f"Error running with scenario: {config.name}:\n{repr(e)}")
                result = None

            # Memoize
            all_results[config.hash] = {
                "metadata": BenchmarkMetadata(
                    model_id=model_id,
                    branch_name=self.branch_name,
                    commit_id=self.commit_id,
                    commit_message=self.commit_message,
                    success=result is not None,
                ),
                "measurements": result if result is not None else BenchmarkResult(),
                "config": config,
            }

            # Cleanup model and save results
            self.cleanup()
            self.save_results(model_id, all_results, timestamp=timestamp, summarized=summarized)

        if len(all_results) < 1:
            raise RuntimeError("No benchmark was run successfully")

        if pretty_print_summary:
            if not self._is_primary_process():
                return (timestamp, all_results)
            print()
            print("=" * 100)
            print(f"Finished benchmarks in {time.perf_counter() - start_time:.2f} seconds")
            print(f"Total number of benchmarks: {len(all_results)}")
            print("First run metadata:")
            first_key = list(all_results.keys())[0]
            first_metadata = all_results[first_key]["metadata"].to_dict()
            hardware_info = first_metadata.pop("hardware_info")
            pretty_print_dict(first_metadata | hardware_info, tabs=1)
            for result in all_results.values():
                print("=" * 100)
                print(f"Config: {result['config'].infer_name(compact=False)}\n")
                result["measurements"].pprint(
                    batch_size=result["config"].batch_size,
                    num_generated_tokens=result["config"].num_tokens_to_generate,
                    tabs=1,
                )
            print("=" * 100)

        return (timestamp, all_results)