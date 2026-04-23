def read_dir(args: argparse.Namespace) -> tuple[dict[str, dict[str, Any]], str]:
    gc.disable()
    prefix = args.prefix
    details = {}
    t0 = time.time()
    version = ""
    filecount = 0
    if not os.path.isdir(args.trace_dir):
        raise AssertionError(f"folder {args.trace_dir} does not exist")
    for root, _, files in os.walk(args.trace_dir):
        if prefix is None:
            prefix = _determine_prefix(files)
        for f in files:
            if (offset := f.find(prefix)) == -1:
                continue
            details[f] = read_dump(f[:offset] + prefix, os.path.join(root, f))
            filecount += 1
            if not version:
                version = str(details[f]["version"])
    tb = time.time()
    if len(details) <= 0:
        raise AssertionError(
            f"no files loaded from {args.trace_dir} with prefix {prefix}"
        )
    logger.debug("loaded %s files in %ss", filecount, tb - t0)
    return details, version