def _output_json_for_dashboard(
    experiments,
    output_file,
    benchmark_name="PyTorch operator microbenchmark",
):
    """
    Write the result into JSON format for PyTorch OSS dashboard.
    The JSON format is defined at
    https://github.com/pytorch/pytorch/wiki/How-to-integrate-with-PyTorch-OSS-benchmark-database

    Args:
        experiments: List of experiment results
        output_file: Path to output JSON file
        benchmark_name: Name of the benchmark
    """
    if not experiments:
        return

    import math
    import platform
    from dataclasses import asdict, dataclass
    from typing import Any

    # Prepare headers and records for JSON output
    records = []
    for experiment in experiments:
        config = experiment.config
        results_dict = (
            experiment.results
        )  # This is a dict: backend -> ExperimentResults

        # Process each backend result
        for backend, results in results_dict.items():
            # Skip backends that were not run (NaN results)
            if math.isnan(results.fwd_time):
                continue

            # Extract data from experiment
            test_name = f"{backend}_{config.attn_type}_"
            input_config = f"shape: {config.shape}, dtype: {config.dtype}"

            # Determine mode based on backward pass
            mode = "training" if config.calculate_bwd_time else "inference"

            # Extract dtype
            dtype = (
                str(config.dtype).split(".")[1]
                if "." in str(config.dtype)
                else str(config.dtype)
            )

            # Determine device
            device = "cuda"

            # Get device architecture
            device_arch = (
                torch.cuda.get_device_name(0)
                if device == "cuda"
                else platform.processor()
                if device == "cpu"
                else "unknown"
            )

            # Create dataclasses for JSON structure
            @dataclass
            class BenchmarkInfo:
                name: str
                mode: str | None
                dtype: str
                extra_info: dict[str, Any]

            @dataclass
            class ModelInfo:
                name: str
                type: str
                origins: list[str]
                extra_info: dict[str, Any]

            @dataclass
            class MetricInfo:
                name: str
                unit: str
                benchmark_values: list[float]
                target_value: float | None

            @dataclass
            class BenchmarkRecord:
                benchmark: BenchmarkInfo
                model: ModelInfo
                metric: MetricInfo

            operator_name = backend_to_operator_name.get(backend, backend)

            # Benchmark extra info
            benchmark_extra_info = {
                "input_config": input_config,
                "device": device,
                "arch": device_arch,
                "operator_name": operator_name,
                "attn_type": config.attn_type,
                "shape": str(config.shape),
                "max_autotune": config.max_autotune,
            }
            # Add record for forward latency
            record_fwd_latency = BenchmarkRecord(
                benchmark=BenchmarkInfo(
                    name=benchmark_name,
                    mode=mode,
                    dtype=dtype,
                    extra_info=benchmark_extra_info,
                ),
                model=ModelInfo(
                    name=test_name + str(config.shape),
                    type="attention-benchmark",
                    origins=["pytorch"],
                    extra_info={
                        "operator_name": operator_name,
                        "attn_type": config.attn_type,
                    },
                ),
                metric=MetricInfo(
                    name="forward latency",
                    unit="us",
                    benchmark_values=[results.fwd_time],
                    target_value=None,
                ),
            )
            records.append(asdict(record_fwd_latency))

            # Add record for forward memory bandwidth (if available)
            if config.cal_bandwidth:
                record_fwd_bandwidth = BenchmarkRecord(
                    benchmark=BenchmarkInfo(
                        name=benchmark_name,
                        mode=mode,
                        dtype=dtype,
                        extra_info=benchmark_extra_info,
                    ),
                    model=ModelInfo(
                        name=test_name + str(config.shape),
                        type="attention-benchmark",
                        origins=["pytorch"],
                        extra_info={
                            "operator_name": operator_name,
                        },
                    ),
                    metric=MetricInfo(
                        name="memory bandwidth",
                        unit="TB/s",
                        benchmark_values=[calculate_bandwidth(config, results, "fwd")],
                        target_value=None,
                    ),
                )
                records.append(asdict(record_fwd_bandwidth))

            # Add record for forward TFLOPS (if available)
            if config.cal_bandwidth:
                record_fwd_tflops = BenchmarkRecord(
                    benchmark=BenchmarkInfo(
                        name=benchmark_name,
                        mode=mode,
                        dtype=dtype,
                        extra_info=benchmark_extra_info,
                    ),
                    model=ModelInfo(
                        name=test_name + str(config.shape),
                        type="attention-benchmark",
                        origins=["pytorch"],
                        extra_info={
                            "operator_name": operator_name,
                        },
                    ),
                    metric=MetricInfo(
                        name="tflops",
                        unit="TFLOPS/s",
                        benchmark_values=[calculate_tflops(config, results)],
                        target_value=None,
                    ),
                )
                records.append(asdict(record_fwd_tflops))

            # Add record for backward latency (if available and not NaN)
            if (
                config.calculate_bwd_time
                and results.bwd_time is not None
                and not math.isnan(results.bwd_time)
            ):
                record_bwd_latency = BenchmarkRecord(
                    benchmark=BenchmarkInfo(
                        name=benchmark_name,
                        mode=mode,
                        dtype=dtype,
                        extra_info=benchmark_extra_info,
                    ),
                    model=ModelInfo(
                        name=test_name + str(config.shape),
                        type="attention-benchmark",
                        origins=["pytorch"],
                        extra_info={
                            "operator_name": operator_name,
                        },
                    ),
                    metric=MetricInfo(
                        name="backward latency",
                        unit="us",
                        benchmark_values=[results.bwd_time],
                        target_value=None,
                    ),
                )
                records.append(asdict(record_bwd_latency))

    # Write all records to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)