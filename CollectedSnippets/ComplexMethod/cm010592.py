def main(args):
    env_before = set(os.environ.keys())
    if platform.system() in ["Windows", "Darwin"]:
        raise RuntimeError(f"{platform.system()} is not supported!!!")

    if args.log_path:
        os.makedirs(args.log_path, exist_ok=True)
    else:
        args.log_path = os.devnull

    if args.latency_mode and args.throughput_mode:
        raise RuntimeError(
            "Either args.latency_mode or args.throughput_mode should be set"
        )

    if not args.no_python and not args.program.endswith(".py"):
        raise RuntimeError(
            'For non Python script, you should use "--no-python" parameter.'
        )

    # Verify LD_PRELOAD
    if "LD_PRELOAD" in os.environ:
        lst_valid = []
        tmp_ldpreload = os.environ["LD_PRELOAD"]
        for item in tmp_ldpreload.split(":"):
            matches = glob.glob(item)
            if len(matches) > 0:
                lst_valid.append(item)
            else:
                logger.warning("%s doesn't exist. Removing it from LD_PRELOAD.", item)
        if len(lst_valid) > 0:
            os.environ["LD_PRELOAD"] = ":".join(lst_valid)
        else:
            os.environ["LD_PRELOAD"] = ""

    launcher = _Launcher()
    launcher.launch(args)
    for x in sorted(set(os.environ.keys()) - env_before):
        logger.debug("%s=%s", x, os.environ[x])