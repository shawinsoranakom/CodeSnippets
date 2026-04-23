def cmd_repro(args):
    run_ids = _resolve_head_runs(args)

    # Fetch perf data to discover configs
    auto_discovered = not hasattr(args, "_run_ids") and not args.device
    all_perf: list[PerfData] = []
    metas: list[RunMeta] = []
    for device, run_id in list(run_ids.items()):
        print(f"Fetching run {run_id} ({device})...")
        metas.append(fetch_run_meta(run_id))
        perf = fetch_run_perf(
            run_id,
            args.attempt,
            no_cache=False,
            device=device,
            allow_empty=auto_discovered,
        )
        all_perf.extend(perf)

    all_perf = filter_perf(all_perf, args)
    if not all_perf:
        print("No configs matched filters.")
        sys.exit(1)

    print_run_header("REPRO", metas)

    configs_seen: dict[str, str] = {}  # config_name → suite
    for perf in all_perf:
        configs_seen[perf.config] = perf.suite

    count = 0
    commands: list[str] = []
    for config in sorted(configs_seen):
        suite = configs_seen[config]
        cmd = config_to_command(config, suite, args.model)
        if not cmd:
            continue
        commands.append(f"# {config}\n{cmd}")
        count += 1

    print(f"\nReproducible commands ({count} configs):\n")
    for cmd in commands:
        print(f"{cmd}\n")