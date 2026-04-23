def parse_csvs(csv_pairs: list[tuple[str, str]], device: str = "") -> list[PerfData]:
    grouped: dict[str, list[ModelResult]] = defaultdict(list)

    for csv_name, content in csv_pairs:
        # csv_name like: inductor_with_cudagraphs_huggingface_amp_training_cuda_performance.csv
        config = csv_name.replace("_performance.csv", "")
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            try:
                speedup = float(row.get("speedup", 0))
            except (ValueError, TypeError):
                continue
            grouped[config].append(
                ModelResult(
                    name=row.get("name", "?"),
                    speedup=speedup,
                    abs_latency=float(row.get("abs_latency", 0) or 0),
                    compilation_latency=float(row.get("compilation_latency", 0) or 0),
                    compression_ratio=float(row.get("compression_ratio", 0) or 0),
                    eager_peak_mem=float(row.get("eager_peak_mem", 0) or 0),
                    dynamo_peak_mem=float(row.get("dynamo_peak_mem", 0) or 0),
                    config=config,
                    device=device,
                )
            )

    return [
        PerfData(config=k, models=v, device=device) for k, v in sorted(grouped.items())
    ]