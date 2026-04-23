def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flake8 wrapper linter.",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "--flake8-plugins-path",
        help="FLAKE8_PLUGINS_PATH env value",
    )
    parser.add_argument(
        "--severity",
        action="append",
        help="map code to severity (e.g. `B950:advice`)",
    )
    parser.add_argument(
        "--retries",
        default=3,
        type=int,
        help="times to retry timed out flake8",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="verbose logging",
    )
    parser.add_argument(
        "filenames",
        nargs="+",
        help="paths to lint",
    )
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

    flake8_plugins_path = (
        None
        if args.flake8_plugins_path is None
        else os.path.realpath(args.flake8_plugins_path)
    )

    severities: dict[str, LintSeverity] = {}
    if args.severity:
        for severity in args.severity:
            parts = severity.split(":", 1)
            if len(parts) != 2:
                raise AssertionError(f"invalid severity `{severity}`")
            severities[parts[0]] = LintSeverity(parts[1])

    lint_messages = check_files(
        args.filenames, flake8_plugins_path, severities, args.retries
    )
    for lint_message in lint_messages:
        print(json.dumps(lint_message._asdict()), flush=True)