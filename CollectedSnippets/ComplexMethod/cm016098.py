def speedup_experiment(args, model_iter_fn, model, example_inputs, **kwargs):
    """
    Measure speedups over eager.

    Writes to ./speedups.csv
    """
    timings = np.zeros((args.repeat, 2), np.float64)
    # if we randomize the input, we should also check the result is correct
    should_randomize_input = args.randomize_input

    import contextlib

    from torch._inductor.utils import maybe_profile

    @contextlib.contextmanager
    def maybe_mark_profile(*args, **kwargs):
        prof: torch.profiler.profile = kwargs.pop("p", None)
        mark = kwargs.pop("mark", None)
        if prof:
            with torch.profiler.record_function(mark):
                yield
        else:
            yield

    times = args.iterations_per_run

    # Use higher tolerance for XLA since XLA cause numerical instability when
    # graph size changes
    tolerance = args.xla_tolerance if args.trace_on_xla else 1e-4
    torch._dynamo.config.repro_tolerance = tolerance

    with maybe_profile(args.export_profiler_trace, **args.profile_details) as p:
        if args.export_aot_inductor:
            frozen_model_iter_fn = export_aot_inductor(
                model, example_inputs, args.inductor_compile_mode
            )
        elif args.export_nativert:
            frozen_model_iter_fn = export_nativert(model, example_inputs)
        elif args.torchscript_jit_trace:
            frozen_model_iter_fn = torchscript_jit_trace(model, example_inputs)
        elif args.aot_precompile:
            frozen_model_iter_fn = aot_precompile(model, example_inputs)
        else:
            if kwargs["hf_llm"]:
                # If it's an llm, we want to optimize model.forward, and use
                # the generate function
                model.forward = torch._dynamo.run(model)
                frozen_model_iter_fn = model_iter_fn
            else:
                frozen_model_iter_fn = torch._dynamo.run(model_iter_fn)

        for rep in trange(args.repeat, desc="running benchmark"):
            inputs = (
                randomize_input(copy.deepcopy(example_inputs))
                if should_randomize_input
                else example_inputs
            )
            # need call mark_step to perform the computation
            # on randomize_input. Otherwise the first call using the
            # inputs will incur high penalty then the next one.
            maybe_mark_step(args)

            # interleave the runs to handle frequency scaling and load changes
            with (
                maybe_mark_profile(p=p, mark="expected"),
                torch.compiler.set_stance("force_eager"),
            ):
                timings[rep, 0], expected_output = timed(
                    model,
                    model_iter_fn,
                    inputs,
                    return_result=True,
                    times=times,
                    collect_outputs=args.collect_outputs,
                    batch_size=kwargs.get("batch_size"),
                )

            # call mark_step between the 2 calls to make the comparison fair.
            maybe_mark_step(args)

            with maybe_mark_profile(p=p, mark="actual"):
                timings[rep, 1], actual_output = timed(
                    model,
                    frozen_model_iter_fn,
                    inputs,
                    return_result=True,
                    times=times,
                    collect_outputs=args.collect_outputs,
                )

    if args.export_profiler_trace:
        name = args.profiler_trace_name + "_" + model.name
        if hasattr(args, "rank"):
            name += f"_rank_{args.rank}"
        if args.export_perfdoctor and trace_handler:
            trace_handler(name, p)
        else:
            name += ".json"
            name = os.path.join(torch._dynamo.config.base_dir, name)
            p.export_chrome_trace(name)

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

    output_signpost(
        dict(zip(headers, row)),
        args,
        get_suite_from_model_iter_fn(model_iter_fn),
    )

    return msg