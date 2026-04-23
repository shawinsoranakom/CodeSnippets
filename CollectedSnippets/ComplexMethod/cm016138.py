def cmd_summary(args):
    attempt = args.attempt
    metric = METRICS[args.metric]

    head_run_ids = _resolve_head_runs(args)

    # Fetch head runs
    auto_discovered = not hasattr(args, "_run_ids") and not args.device
    head_metas: list[RunMeta] = []
    head_perf: list[PerfData] = []
    for device, run_id in list(head_run_ids.items()):
        print(f"Fetching head run {run_id} ({device})...")
        perf = fetch_run_perf(
            run_id,
            attempt,
            args.no_cache,
            device=device,
            allow_empty=auto_discovered,
        )
        if not perf:
            del head_run_ids[device]
            continue
        head_metas.append(fetch_run_meta(run_id))
        head_perf.extend(perf)

    head_perf = filter_perf(head_perf, args)
    if not head_perf:
        print("No configs matched filters.")
        sys.exit(1)

    head_configs = [p.qualified_config for p in head_perf]

    # Baseline comparison mode
    if args.baseline and args.baseline.lower() != "none":
        base_metas: list[RunMeta] = []
        base_perf: list[PerfData] = []

        for device, head_run_id in head_run_ids.items():
            if args.baseline == "latest":
                baseline_id = resolve_baseline(head_run_id)
            else:
                try:
                    baseline_id = int(args.baseline)
                except ValueError:
                    baseline_id = resolve_run(args.baseline, device)

            print(f"Fetching baseline run {baseline_id} ({device})...")
            base_data = fetch_run_perf(
                baseline_id,
                attempt,
                args.no_cache,
                device=device,
                allow_empty=auto_discovered,
            )
            if not base_data:
                continue
            base_metas.append(fetch_run_meta(baseline_id))
            base_perf.extend(base_data)

        base_perf = filter_perf(base_perf, args)
        if not base_perf:
            print("No baseline configs matched filters.")
            sys.exit(1)

        print_run_header("HEAD", head_metas, head_configs)
        print_run_header("BASE", base_metas, [p.qualified_config for p in base_perf])
        print()

        deltas, config_aggs = compute_deltas(head_perf, base_perf, metric)
        if not deltas:
            print("No matching models between head and baseline.")
            sys.exit(1)

        print_comparison_table(config_aggs, metric)
        print_regressions(deltas, metric, args.top)
        render_delta_scurve(deltas, metric)
        return

    # Absolute mode (no baseline)
    print_run_header("RUN", head_metas, head_configs)
    print()

    print_summary_table(head_perf, metric)
    grouped = group_perf(head_perf, args.group_by)
    for perf in grouped:
        print_worst_offenders(perf, metric, args.top)
        render_scurve(perf, metric, args.top)