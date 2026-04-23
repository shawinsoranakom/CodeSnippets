def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Ruff linter. Linter code: {LINTER_CODE}. Use with RUFF-FIX to auto-fix issues.",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to the `pyproject.toml` or `ruff.toml` file to use for configuration",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Explain a rule",
    )
    parser.add_argument(
        "--show-disable",
        action="store_true",
        help="Show how to disable a lint message",
    )
    parser.add_argument(
        "--timeout",
        default=90,
        type=int,
        help="Seconds to wait for ruff",
    )
    parser.add_argument(
        "--severity",
        action="append",
        help="map code to severity (e.g. `F401:advice`). This option can be used multiple times.",
    )
    parser.add_argument(
        "--no-fix",
        action="store_true",
        help="Do not suggest fixes",
    )
    add_default_options(parser)
    args = parser.parse_args()

    logging.basicConfig(
        format="<%(threadName)s:%(levelname)s> %(message)s",
        level=logging.NOTSET
        if args.verbose
        else logging.DEBUG
        if len(args.filenames) < 1000
        else logging.INFO,
        stream=sys.stderr,
    )

    severities: dict[str, LintSeverity] = {}
    if args.severity:
        for severity in args.severity:
            parts = severity.split(":", 1)
            if len(parts) != 2:
                raise AssertionError(f"invalid severity `{severity}`")
            severities[parts[0]] = LintSeverity(parts[1])

    lint_messages = check_files(
        args.filenames,
        severities=severities,
        config=args.config,
        retries=args.retries,
        timeout=args.timeout,
        explain=args.explain,
        show_disable=args.show_disable,
    )
    for lint_message in lint_messages:
        lint_message.display()

    if args.no_fix or not lint_messages:
        # If we're not fixing, we can exit early
        return

    files_with_lints = {lint.path for lint in lint_messages if lint.path is not None}
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=os.cpu_count(),
        thread_name_prefix="Thread",
    ) as executor:
        futures = {
            executor.submit(
                check_file_for_fixes,
                path,
                config=args.config,
                retries=args.retries,
                timeout=args.timeout,
            ): path
            for path in files_with_lints
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                for lint_message in future.result():
                    lint_message.display()
            except Exception:  # Catch all exceptions for lintrunner
                logging.critical('Failed at "%s".', futures[future])
                raise