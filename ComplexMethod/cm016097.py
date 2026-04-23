def latency_experiment_summary(suite_name, args, model, timings, **kwargs):
    median = np.median(timings, axis=0)
    speedup = median[0] / median[1]
    if args.dump_raw_metrics:
        np.save(
            f"{output_filename[:-4]}-raw_timings-{current_name}-{current_device}.npy",
            timings,
        )

    first_headers = ["dev", "name", "batch_size"]
    first_fields = [current_device, current_name, current_batch_size]
    if "tag" in kwargs:
        first_headers.append("tag")
        first_fields.append(kwargs["tag"])
    headers = first_headers + ["speedup", "abs_latency"]
    row = first_fields + [float(speedup), median[1] * 1000]
    msg = f"{speedup:.3f}x"
    if getattr(args, "_print_latency_ms", False):
        msg = f"{median[0] * 1000:.4f} ms, {median[1] * 1000:.4f} ms, {msg}"
    if args.baseline:
        headers.extend(
            [
                "baseline",
                "speedup_vs_baseline",
            ]
        )
        df = pd.read_csv(args.baseline)
        try:
            baseline_speedup = df[df["name"] == current_name]["speedup"].item()
            row.extend([baseline_speedup, speedup / baseline_speedup])
            msg = f"{baseline_speedup:.3f}x -> {speedup:.3f}x [{speedup / baseline_speedup:.3f}x]"
        except (KeyError, ZeroDivisionError):
            row.extend(
                [
                    0.0,
                    0.0,
                ]
            )
    if "compilation_latency" in kwargs:
        headers += [
            "compilation_latency",
            "compression_ratio",
            "eager_peak_mem",
            "dynamo_peak_mem",
        ]
        row.append(kwargs["compilation_latency"])
        row.append(kwargs["compression_ratio"])
        row.append(kwargs["eager_peak_mem"])
        row.append(kwargs["dynamo_peak_mem"])

    if "cache_lookup_latency" in kwargs:
        headers.append("cache_lookup_latency")
        row.append(kwargs["cache_lookup_latency"])

    if "dynamo_stats" in kwargs:
        for k, v in kwargs["dynamo_stats"].items():
            headers.append(k)
            row.append(v)
    write_outputs(
        output_filename,
        headers,
        row,
    )
    c_headers, c_data = torch._dynamo.utils.compile_times(repr="csv", aggregate=True)
    if output_filename.find(".csv") <= 0:
        raise AssertionError(
            f"expected output_filename to be a .csv, but got {output_filename}"
        )
    write_outputs(
        output_filename[:-4] + "_compilation_metrics.csv",
        first_headers + c_headers,
        first_fields + c_data,
    )

    # Hypothetically you can use this from other places, but it's currently
    # inaccessible, and when this assert fails you need to update the
    # event_name here to account for the other cases you are using this
    if not any([args.quantization, args.optimus]):
        raise AssertionError("expected args.quantization or args.optimus to be set")
    output_signpost(
        dict(zip(headers, row)),
        args,
        suite_name,
    )

    return msg