def output_signpost(data, args, suite, error=None):
    from torch.utils._stats import simple_call_counter

    data = data.copy()

    if "name" not in data:
        data["name"] = current_name

    if "dev" not in data:
        data["dev"] = current_device

    filtered_args = vars(args).copy()
    # I generated this list by reading through all the configs and dropping
    # ones that looked irrelevant or redundant
    for k in [
        "filter",
        "exclude",
        "exclude_exact",
        "dump_raw_metrics",
        "log_operator_inputs",
        "distributed_master_port",
        "skip_accuracy_check",
        "generate_aot_autograd_stats",
        "output",
        "output_directory",
        "disable_output",
        "export_profiler_trace",
        "profiler_trace_name",
        "explain",
        "stats",
        "print_memory",
        "print_compilation_time",
        "print_dataframe_summary",
        "print_graph_breaks",
        "log_graph_breaks",
        "timing",
        "progress",
        "timeout",
        "per_process_memory_fraction",
        "minify",
        "verbose",
        "quiet",
        "print_fx",
        "print_aten_ops",
        "log_conv_args",
        "recompile_profiler",
        "find_batch_sizes",
        # Redundant
        "batch_size",
        "batch_size_file",
        "only",
        "diff_branch",
        "tag",
        "coverage",
        "overhead",
        "speedup_dynamo_ts",
        "speedup_fx2trt",
        "speedup_fx2trt_fp16",
        "accuracy",
        "performance",
        "tolerance",
    ]:
        del filtered_args[k]

    event_name = "unknown"
    if args.accuracy:
        event_name = "accuracy"
    elif args.quantization:
        event_name = "quantization"
    elif args.performance:
        event_name = "performance"

    from torch._dynamo.utils import calculate_time_spent, compilation_time_metrics

    wall_time_by_phase = calculate_time_spent()

    open_source_signpost(
        subsystem="dynamo_benchmark",
        name=event_name,
        parameters=json.dumps(
            {
                **data,
                # TODO: Arguably the rest of these should be in the CSV too
                "suite": suite,
                # Better than using compile_times utils directly
                # NB: Externally, compilation_metrics colloquially refers to
                # the coarse-grained phase timings, even though internally
                # they are called something else
                "compilation_metrics": wall_time_by_phase,
                "agg_compilation_metrics": {
                    k: sum(v) for k, v in compilation_time_metrics.items()
                },
                "detailed_compilation_metrics": compilation_time_metrics,
                "simple_call_counter": simple_call_counter,
                # NB: args has training vs inference
                "args": filtered_args,
                "error": error,
            }
        ),
    )

    return wall_time_by_phase["total_wall_time"]