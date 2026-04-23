def cmd_launch(args):
    ref = args.ref or git("rev-parse", "--abbrev-ref", "HEAD")
    if ref == "HEAD":
        ref = git("rev-parse", "HEAD")

    extra_flags = build_dispatch_inputs(args)
    launched: dict[str, int] = {}
    for device in args.device:
        if device not in WORKFLOWS:
            print(f"Unknown device: {device}", file=sys.stderr)
            sys.exit(1)
        run_id = dispatch_one(device, ref, extra_flags)
        if run_id:
            launched[device] = run_id

    if (args.wait or args.wait_and_summarize) and launched:
        succeeded = wait_for_runs(launched)
        if args.wait_and_summarize and succeeded:
            # Use the first device's run ID as the positional arg; pass all
            # device→run_id pairs via _run_ids so cmd_summary skips resolution.
            first_run = next(iter(succeeded.values()))
            summary_args = argparse.Namespace(
                run_id=str(first_run),
                device=list(succeeded.keys()),
                _run_ids=succeeded,
                baseline="latest",
                metric="speedup",
                top=5,
                config=None,
                suite=None,
                mode=None,
                group_by=None,
                attempt=1,
                no_cache=False,
            )
            print(f"\n{'=' * 70}")
            print("Summary")
            print(f"{'=' * 70}")
            cmd_summary(summary_args)