def benchmark(
    suite,
    op,
    dtype,
    max_samples,
    accuracy_checking,
    repeats,
    inductor_config,
    measure_nvfuser,
    device,
    inp_file,
    start_idx,
    channels_last,
    profile,
):
    warnings.filterwarnings("ignore", module="torch.jit._check")
    torch.set_float32_matmul_precision("high")
    global profile_enabled

    if inp_file is not None:
        loader = OperatorInputsLoader(inp_file)
    else:
        if suite not in ("timm", "huggingface", "torchbench"):
            raise AssertionError(
                f"suite must be one of 'timm', 'huggingface', 'torchbench', but got '{suite}'"
            )
        if suite == "timm":
            loader = OperatorInputsLoader.get_timm_loader()
        elif suite == "huggingface":
            loader = OperatorInputsLoader.get_huggingface_loader()
        else:
            loader = OperatorInputsLoader.get_torchbench_loader()

    if dtype not in ("float16", "float32"):
        raise AssertionError(f"dtype must be 'float16' or 'float32', but got '{dtype}'")

    inductor_configs = [{}]
    backend_names = ["inductor"]
    for name in inductor_config or ():
        backend_names.append(name)
        inductor_configs.append(inductor_config_options[name])
    if measure_nvfuser:
        backend_names.append("nvfuser")

    compare2 = len(backend_names) == 2
    if compare2:
        a, b = backend_names
        backend_names.append(f"{a}/{b}")

    output_fd = None
    output_csv = None
    if op == "all":
        filename = f"operatorbench_{suite}_{dtype}.csv"
        with open(filename, "w") as output_fd:
            output_csv = csv.writer(output_fd)
            output_csv.writerow(
                [
                    "operator",
                    *[
                        f"{a} {b}"
                        for a, b in itertools.product(
                            backend_names,
                            [f"{x * 100:.0f}th" for x in quantiles_thresholds],
                        )
                    ],
                    "elapsed",
                    *map("{} abs".format, ["eager", *backend_names]),
                ]
            )

    dtype = torch.float16 if dtype == "float16" else torch.float32

    if op == "all":
        ops = loader.get_all_ops()
    else:
        ops = [eval(op)]

    max_samples = max_samples + start_idx
    profile_enabled = profile

    for operator in ops:
        if skip_operator(operator):
            continue
        start = time.perf_counter()
        inp_gen = loader.get_inputs_for_operator(operator, dtype=dtype, device=device)
        timings = []
        inputs_list = []
        for _ in range(min(max_samples, 1000000)):
            try:
                inps = next(inp_gen)
                inputs_list.append(inps)
            except StopIteration:
                break

        profiler_context = (
            torch.profiler.profile(
                activities=[
                    torch.profiler.ProfilerActivity.CPU,
                    torch.profiler.ProfilerActivity.CUDA,
                ],
                record_shapes=False,
                profile_memory=False,
                on_trace_ready=torch.profiler.tensorboard_trace_handler(
                    f"./log/operator_{operator}", use_gzip=True
                ),
            )
            if profile_enabled
            else nullcontext()
        )
        with profiler_context:
            for i, inps in enumerate(tqdm(inputs_list[start_idx:], desc=str(operator))):
                if inps is None:
                    break
                args, kwargs = inps
                if channels_last:
                    args, kwargs = tree_map_only(
                        torch.Tensor, to_channels_last, (args, kwargs)
                    )
                try:
                    with maybe_record_function(f"iter_{i}"):
                        # aten, nvfuser, inductor
                        timings.append(
                            microbenchmark(
                                operator,
                                args,
                                kwargs,
                                accuracy_checking,
                                repeats,
                                inductor_configs,
                                measure_nvfuser,
                                device,
                            )
                        )
                except Exception as e:
                    print(f"error {operator} input {i}: {type(e).__name__}: {e}")
                    # comment out this line to avoid blocking other tests
                    # raise e

        if not timings:
            continue

        timings = np.stack(timings)
        speedups = [
            quantiles(timings[:, 0] / timings[:, x]) for x in range(1, timings.shape[1])
        ]
        if compare2:
            speedups.append(quantiles(timings[:, 1] / timings[:, 2]))
        if len(backend_names) != len(speedups):
            raise AssertionError(
                f"Expected {len(backend_names)} speedups for {len(backend_names)} backends, but got {len(speedups)}"
            )

        row = [f"{operator}"]
        sys.stdout.write(f"{operator}: ")
        for backend, (low, mid, high) in zip(backend_names, speedups):
            sys.stdout.write(f"{backend}={mid:.4f}x ({low:.4f}-{high:.4f}) ")
            row.extend(map("{:.6f}".format, [low, mid, high]))
        elapsed = time.perf_counter() - start
        row.append(f"{elapsed:1f}")
        row.extend(map("{:.8f}".format, np.mean(timings, axis=0).tolist()))
        sys.stdout.write(f"took {elapsed:.0f}s\n")
        sys.stdout.flush()
        if output_csv:
            output_csv.writerow(row)
            output_fd.flush()

    if output_fd:
        print(f"Wrote {filename}")
        output_fd.close()