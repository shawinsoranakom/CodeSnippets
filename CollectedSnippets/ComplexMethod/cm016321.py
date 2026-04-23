def main() -> None:
    parser = argparse.ArgumentParser(
        description="clang-tidy wrapper linter.",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "--binary",
        required=True,
        help="clang-tidy binary path",
    )
    parser.add_argument(
        "--build-dir",
        "--build_dir",
        required=True,
        help=(
            "Where the compile_commands.json file is located. "
            "Gets passed to clang-tidy -p"
        ),
    )
    parser.add_argument(
        "--std",
        default=None,
        help=(
            "C++ standard to use for compilation (e.g., c++17, c++20). "
            "If not specified, uses the standard from compile_commands.json."
        ),
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

    if not os.path.exists(args.binary):
        err_msg = LintMessage(
            path="<none>",
            line=None,
            char=None,
            code="CLANGTIDY",
            severity=LintSeverity.ERROR,
            name="command-failed",
            original=None,
            replacement=None,
            description=(
                f"Could not find clang-tidy binary at {args.binary},"
                " you may need to run `lintrunner init`."
            ),
        )
        print(json.dumps(err_msg._asdict()), flush=True)
        sys.exit(0)

    abs_build_dir = Path(args.build_dir).resolve()

    # Get the absolute path to clang-tidy and use this instead of the relative
    # path such as .lintbin/clang-tidy. The problem here is that os.chdir is
    # per process, and the linter uses it to move between the current directory
    # and the build folder. And there is no .lintbin directory in the latter.
    # When it happens in a race condition, the linter command will fails with
    # the following no such file or directory error: '.lintbin/clang-tidy'
    binary_path = os.path.abspath(args.binary)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=os.cpu_count(),
        thread_name_prefix="Thread",
    ) as executor:
        futures = {
            executor.submit(
                check_file,
                filename,
                binary_path,
                abs_build_dir,
                args.std,
            ): filename
            for filename in args.filenames
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                for lint_message in future.result():
                    print(json.dumps(lint_message._asdict()), flush=True)
            except Exception:
                logging.critical('Failed at "%s".', futures[future])
                raise