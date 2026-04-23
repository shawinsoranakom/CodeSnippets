def main() -> None:
    parser = argparse.ArgumentParser(
        description="Format files with clang-format.",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "--binary",
        required=True,
        help="clang-format binary path",
    )
    parser.add_argument(
        "--retries",
        default=3,
        type=int,
        help="times to retry timed out clang-format",
    )
    parser.add_argument(
        "--timeout",
        default=90,
        type=int,
        help="seconds to wait for clang-format",
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

    binary = os.path.normpath(args.binary) if IS_WINDOWS else args.binary
    if not Path(binary).exists():
        lint_message = LintMessage(
            path=None,
            line=None,
            char=None,
            code="CLANGFORMAT",
            severity=LintSeverity.ERROR,
            name="init-error",
            original=None,
            replacement=None,
            description=(
                f"Could not find clang-format binary at {binary}, "
                "did you forget to run `lintrunner init`?"
            ),
        )
        print(json.dumps(lint_message._asdict()), flush=True)
        sys.exit(0)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=os.cpu_count(),
        thread_name_prefix="Thread",
    ) as executor:
        futures = {
            executor.submit(check_file, x, binary, args.retries, args.timeout): x
            for x in args.filenames
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                for lint_message in future.result():
                    print(json.dumps(lint_message._asdict()), flush=True)
            except Exception:
                logging.critical('Failed at "%s".', futures[future])
                raise