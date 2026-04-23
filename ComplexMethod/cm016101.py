def main(runner, original_dir=None, args=None):
    if original_dir:
        os.chdir(original_dir)
    args = parse_args() if not args else parse_args(args)
    if args.baseline:
        args.baseline = os.path.abspath(args.baseline)

    if should_diff_branch(args):
        import git

        # We do this here so we error out earlier if there's an issue
        repo = git.Repo()
        if repo.is_dirty():
            raise RuntimeError(
                "--diff-branch called on dirty branch. Commit, stash, or reset."
            )
        main_branch = repo.active_branch.name
        if main_branch == args.diff_branch:
            raise RuntimeError(
                f"--diff-branch: current branch is same as {args.diff_branch} branch, what are you diffing?"
            )

    with maybe_fresh_cache(args):
        if args.caching_precompile:
            os.environ["TORCH_CACHING_PRECOMPILE"] = "1"
            torch._dynamo.config.caching_precompile = True

        args.init_distributed = args.only and args.multiprocess
        if args.init_distributed:
            # NB: Do NOT query device count before CUDA initialization; we're
            # going to overwrite CUDA_VISIBLE_DEVICES and this will result in
            # https://github.com/pytorch/pytorch/issues/107300
            device_count = torch.cuda.device_count()
            if device_count <= 1:
                log.warning(
                    "The use multiprocess flag is set but there are <= 1 devices available."
                )
            # multiprocess path
            args.world_size = device_count
            mp.spawn(
                process_entry, args=(runner, original_dir, args), nprocs=device_count
            )
        elif args.only and args.warm_start_latency:
            # Warm start mode. Enable FX graph caching and perform back-to-back runs in
            # separate processes (but ensure the inductor cache is preserved across runs).
            env = os.environ.copy()
            env["TORCHINDUCTOR_FX_GRAPH_CACHE"] = "1"
            cmd = [sys.executable] + sys.argv
            cmd.remove("--warm-start-latency")

            print(f"Performing cold-start run for {args.only}")
            warmup_cmd = cmd + ["--repeat=1", "--disable-output"]
            subprocess.check_call(warmup_cmd, timeout=args.timeout, env=env)

            print(f"Performing warm-start run for {args.only}")
            subprocess.check_call(cmd, timeout=args.timeout, env=env)
        else:
            # single process path just uses the main process
            args.world_size = 1
            if args.compare_backed_unbacked:
                _run_compare_backed_unbacked(runner, args)
            else:
                process_entry(0, runner, original_dir, args)