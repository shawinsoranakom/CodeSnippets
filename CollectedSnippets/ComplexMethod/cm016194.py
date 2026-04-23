def main() -> None:
    """Main entry point"""
    global LOGGER, VERBOSE
    args = parse_arguments()
    VERBOSE = args.verbose

    status = check_branch(args.subcmd, args.branch)
    if status:
        sys.exit(status)

    pip_source = None
    for toolkit in ("CUDA", "ROCm"):
        accel = toolkit.lower()
        if hasattr(args, accel):
            requested = getattr(args, accel)
            available_sources = {
                src.name[len(f"{accel}-") :]: src
                for src in PIP_SOURCES.values()
                if src.name.startswith(f"{accel}-")
                and PLATFORM in src.supported_platforms
            }
            if not available_sources:
                print(f"No {toolkit} versions available on platform {PLATFORM}.")
                sys.exit(1)
            if requested is not None:
                pip_source = available_sources.get(requested)
                if pip_source is None:
                    print(
                        f"{toolkit} {requested} is not available on platform {PLATFORM}. "
                        f"Available version(s): {', '.join(sorted(available_sources, key=Version))}"
                    )
                    sys.exit(1)
            else:
                pip_source = available_sources[max(available_sources, key=Version)]

    if pip_source is None:
        pip_source = PIP_SOURCES["cpu"]  # always available

    with logging_manager(debug=args.verbose) as logger:
        LOGGER = logger
        venv = Venv(
            prefix=args.prefix,
            pip_source=pip_source,
            base_executable=args.base_executable,
        )
        install(
            venv=venv,
            packages=PACKAGES_TO_INSTALL,
            subcommand=args.subcmd,
            branch=args.branch,
            fresh_venv=args.fresh,
            assume_yes=args.yes,
        )