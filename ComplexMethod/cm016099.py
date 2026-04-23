def baselines(models, model_iter_fn, example_inputs, args):
    """
    Common measurement code across all baseline experiments.
    """
    models = list(models)
    for idx, (name, model) in enumerate(models):
        if idx == 0:
            result0 = model_iter_fn(model, example_inputs)
        elif model is not None:
            try:
                result = model_iter_fn(model, example_inputs)
                if same(result0, result):
                    continue
                print(name, "is INCORRECT")
            except Exception:
                log.exception("error checking %s", name)
            models[idx] = (name, None)
    timings = np.zeros((args.repeat, len(models)), np.float64)
    timings.fill(1.0e10)
    for rep in range(args.repeat):
        for idx, (name, model) in enumerate(models):
            if model is not None:
                try:
                    timings[rep, idx] = timed(model, model_iter_fn, example_inputs)
                except Exception:
                    pass
    pvalue = [
        ttest_ind(timings[:, 0], timings[:, i]).pvalue
        for i in range(1, timings.shape[1])
    ]
    median = np.median(timings, axis=0)
    speedup = median[0] / median[1:]
    for idx, (name, model) in enumerate(models[1:]):
        if model is None:
            speedup[idx] = 0.0
    result = " ".join(
        [
            format_speedup(s, p, m is not None)
            for s, p, m in zip(speedup, pvalue, [m for n, m in models[1:]])
        ]
    )
    write_outputs(
        output_filename,
        ("dev", "name", "batch_size") + tuple(n for n, m in models[1:]),
        [current_device, current_name, current_batch_size]
        + [f"{x:.4f}" for x in speedup],
    )
    return result