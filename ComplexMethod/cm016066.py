def _output_json(
        self,
        perf_list,
        output_file,
        benchmark_name="PyTorch operator benchmark",
    ):
        """
        Write the result into JSON format, so that it can be uploaded to the benchmark database
        to be displayed on OSS dashboard. The JSON format is defined at
        https://github.com/pytorch/pytorch/wiki/How-to-integrate-with-PyTorch-OSS-benchmark-database
        """
        if not perf_list:
            return

        # Prepare headers and records for JSON output
        records = []
        for perf_item in perf_list:
            # Extract data from perf_item
            test_name = perf_item.get("test_name", "unknown")
            input_config = perf_item.get("input_config", "")
            run_type = perf_item.get("run")
            latency = perf_item.get("latency", 0)
            peak_memory = perf_item.get("peak memory", 0)
            memory_bandwidth = perf_item.get("memory bandwidth", 0)
            device = perf_item.get("device", "unknown")
            dtype = perf_item.get("dtype", "torch.float").split(".")[1]
            runtime = perf_item.get("runtime", None)

            # Extract mode based on run_type
            mode = None
            if run_type == "Forward":
                mode = "inference"
            elif run_type == "Backward":
                mode = "training"

            # Extract use_compile from it
            if runtime == "Compile":
                use_compile = True
            elif runtime == "Eager":
                use_compile = False
            else:
                use_compile = None

            device_arch = (
                torch.cuda.get_device_name(0)
                if device == "cuda"
                else platform.processor()
                if device == "cpu"
                else "unknown"
            )

            # Extract operator name from test_name
            operator_name = test_name.split("_")[0]

            # Create the record
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

            # Add record for latency
            record_latency = BenchmarkRecord(
                benchmark=BenchmarkInfo(
                    name=benchmark_name,
                    mode=mode,
                    dtype=dtype,
                    extra_info={
                        "input_config": input_config,
                        "device": device,
                        "arch": device_arch,
                        "use_compile": use_compile,
                        "operator_name": operator_name,
                    },
                ),
                model=ModelInfo(
                    name=test_name,
                    type="micro-benchmark",
                    origins=["pytorch"],
                    extra_info={"operator_name": operator_name},
                ),
                metric=MetricInfo(
                    name="latency",
                    unit="us",
                    benchmark_values=[latency],
                    target_value=None,
                ),
            )
            records.append(asdict(record_latency))

            # Add record for peak memory
            record_memory = copy.deepcopy(record_latency)
            record_memory.metric = MetricInfo(
                name="peak memory",
                unit="KB",
                benchmark_values=[peak_memory],
                target_value=None,
            )
            records.append(asdict(record_memory))

            # Add record for memory bandwidth
            record_memory_bandwidth = copy.deepcopy(record_latency)
            record_memory_bandwidth.metric = MetricInfo(
                name="memory bandwidth",
                unit="GB/s",
                benchmark_values=[memory_bandwidth],
                target_value=None,
            )
            records.append(asdict(record_memory_bandwidth))

        # Write all records to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)