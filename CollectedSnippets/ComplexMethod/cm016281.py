def main() -> None:
    args = parse_args()

    if args.find_python:
        if args.python:
            logger.warning(
                "Both --python and --find-python specified. Using --find-python and ignoring --python."
            )
        pythons = find_python_interpreters(args.find_python)
        if not pythons:
            logger.error(
                "No Python interpreters found with --find-python %s", args.find_python
            )
            sys.exit(1)
        logger.info(
            "Found %d supported Python interpreters: %s",
            len(pythons),
            ", ".join(pythons),
        )
    else:
        pythons = args.python or [sys.executable]

    build_times: dict[str, float] = dict()

    if len(pythons) > 1 and args.destination == "dist/":
        logger.warning(
            "dest is 'dist/' while multiple python versions specified, output will be overwritten"
        )

    for interpreter in pythons:
        with venv(interpreter) as venv_interpreter:
            builder = Builder(venv_interpreter)
            # clean actually requires setuptools so we need to ensure we
            # install requirements before
            builder.install_requirements()
            builder.clean()

            start_time = time.time()

            builder.build_wheel(args.destination)

            end_time = time.time()

            build_times[interpreter_version(venv_interpreter)] = end_time - start_time
    for version, build_time in build_times.items():
        logger.info("Build time (%s): %fs", version, build_time)