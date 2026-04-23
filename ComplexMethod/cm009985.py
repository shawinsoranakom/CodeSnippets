def _process_lintrunner_args(lintrunner_args):
    take = None
    skip = None
    args_iter = iter(arg.strip() for arg in lintrunner_args)
    remaining_args = []
    tee_file = None
    has_paths = False
    has_all_files = False
    for arg in args_iter:
        if _take := _check_arg("--take", arg, args_iter):
            take = set(_take.split(","))
        elif _skip := _check_arg("--skip", arg, args_iter):
            skip = set(_skip.split(","))
        elif _tee_file := _check_arg("--tee-json", arg, args_iter):
            tee_file = _tee_file.strip()
        elif arg == "--all-files":
            has_all_files = True
        else:
            if not arg.startswith("-"):
                has_paths = True
            remaining_args.append(arg)
    return remaining_args, take, skip, tee_file, has_paths, has_all_files