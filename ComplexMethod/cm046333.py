def get_save_dir(args: SimpleNamespace, name: str | None = None) -> Path:
    """Return the directory path for saving outputs, derived from arguments or default settings.

    Args:
        args (SimpleNamespace): Namespace object containing configurations such as 'project', 'name', 'task', 'mode',
            and 'save_dir'.
        name (str | None): Optional name for the output directory. If not provided, it defaults to 'args.name' or the
            'args.mode'.

    Returns:
        (Path): Directory path where outputs should be saved.

    Examples:
        >>> from types import SimpleNamespace
        >>> args = SimpleNamespace(project="my_project", task="detect", mode="train", exist_ok=True)
        >>> save_dir = get_save_dir(args)
        >>> print(save_dir)
        runs/detect/my_project/train
    """
    if getattr(args, "save_dir", None):
        save_dir = args.save_dir
    else:
        from ultralytics.utils.files import increment_path

        project = args.project or ""
        if not Path(project).is_absolute():
            project = (ROOT.parent / "tests/tmp/runs" if TESTS_RUNNING else RUNS_DIR) / args.task / project
        name = name or args.name or f"{args.mode}"
        save_dir = increment_path(Path(project) / name, exist_ok=args.exist_ok if RANK in {-1, 0} else True)

    return Path(save_dir).resolve()