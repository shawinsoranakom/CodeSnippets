def summarize(run_dir, metrics, expand_metrics=False):
    """Produce a summary for each optimum-benchmark launched job's output directory found in `run_dir`.

    Each summary's format is as follows (for `expand_metrics=False`):
    ```
    {
        "model": "google/gemma-2b",
        "commit": "3cd6ed22e4d49219f300f5055e71e3929aba20d7",
        "config": "benchmark.input_shapes.batch_size=1,benchmark.input_shapes.sequence_length=5",
        "metrics": {
            "decode.latency.mean": 1.624666809082031,
            "per_token.latency.mean": 0.012843788806628804,
            "per_token.throughput.value": 77.85864553330948
        }
    }
    ```
    """
    reports = glob.glob(os.path.join(run_dir, "**/benchmark_report.json"), recursive=True)
    report_dirs = [str(Path(report).parent) for report in reports]

    summaries = []
    for report_dir in report_dirs:
        commit = re.search(r"/commit=([^/]+)", report_dir).groups()[0]

        if not os.path.isfile(os.path.join(report_dir, "benchmark.json")):
            continue
        benchmark = Benchmark.from_json(os.path.join(report_dir, "benchmark.json"))
        report = benchmark.report

        model = benchmark.config.backend["model"]

        # This looks like `benchmark.input_shapes.batch_size=1,benchmark.input_shapes.sequence_length=5`.
        # (we rely on the usage of hydra's `${hydra.job.override_dirname}`.)
        benchmark_name = re.sub(f"backend.model={model},*", "", report_dir)
        benchmark_name = str(Path(benchmark_name).parts[-1])
        if benchmark_name.startswith("commit="):
            benchmark_name = benchmark.config.name

        metrics_values = {}
        # post-processing of report: show a few selected/important metric
        for metric in metrics:
            keys = metric.split(".")
            value = report.to_dict()
            current = metrics_values
            for key in keys:
                # Avoid KeyError when a user's specified metric has typo.
                # TODO: Give warnings.
                if key not in value:
                    continue
                value = value[key]

                if expand_metrics:
                    if isinstance(value, dict):
                        if key not in current:
                            current[key] = {}
                            current = current[key]
                    else:
                        current[key] = value

            if not expand_metrics:
                metrics_values[metric] = value

        # show some config information
        print(f"model: {model}")
        print(f"commit: {commit}")
        print(f"config: {benchmark_name}")
        if len(metrics_values) > 0:
            print("metrics:")
            if expand_metrics:
                print(metrics_values)
            else:
                for metric, value in metrics_values.items():
                    print(f"  - {metric}: {value}")
        print("-" * 80)

        summary = {
            "model": model,
            "commit": commit,
            "config": benchmark_name,
            "metrics": metrics_values,
        }
        summaries.append(summary)

        with open(os.path.join(report_dir, "summary.json"), "w") as fp:
            json.dump(summary, fp, indent=4)

    return summaries
