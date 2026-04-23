def run_bench(model_names, bench_args):
    results = []
    for model_name in model_names:
        model_creator = MODELS[model_name]
        inputs, model = model_creator(bench_args)

        print("Benchmarking RecordFunction overhead for", model_name)
        print("Running warmup...", end=" ")
        sys.stdout.flush()
        for _ in range(bench_args.warmup):
            model(*inputs)
        print("finished")

        for num_threads in NUM_THREADS:
            for with_rec_fn in [True, False]:
                torch.autograd._enable_record_function(with_rec_fn)
                torch.autograd._clear_callbacks()
                if with_rec_fn:
                    torch.autograd._set_empty_test_observer(True, 0.0001)

                print(
                    "Running {} RecordFunction, num threads {} ...".format(
                        "with" if with_rec_fn else "without", num_threads
                    ),
                    end=" ",
                )
                sys.stdout.flush()
                timer = benchmark_utils.Timer(
                    stmt="model(*inputs)",
                    globals={"model": model, "inputs": inputs},
                    description=model_name,
                    label="Record function overhead",
                    sub_label=f"with{'' if with_rec_fn else 'out'}_rec_fn, num_threads {num_threads}",
                    num_threads=num_threads,
                )
                result = timer.blocked_autorange(
                    min_run_time=bench_args.timer_min_run_time
                )
                print("finished")
                print(result)
                sys.stdout.flush()
                results.append(result)

    comparison = benchmark_utils.Compare(results)
    comparison.trim_significant_figures()
    comparison.highlight_warnings()
    comparison.print()