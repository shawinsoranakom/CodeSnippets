def main() -> None:
    parser = argparse.ArgumentParser(
        description="grep wrapper linter.",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "--pattern",
        required=True,
        help="pattern to grep for",
    )
    parser.add_argument(
        "--allowlist-pattern",
        help="if this pattern is true in the file, we don't grep for pattern",
    )
    parser.add_argument(
        "--linter-name",
        required=True,
        help="name of the linter",
    )
    parser.add_argument(
        "--match-first-only",
        action="store_true",
        help="only match the first hit in the file",
    )
    parser.add_argument(
        "--error-name",
        required=True,
        help="human-readable description of what the error is",
    )
    parser.add_argument(
        "--error-description",
        required=True,
        help="message to display when the pattern is found",
    )
    parser.add_argument(
        "--replace-pattern",
        help=(
            "the form of a pattern passed to `sed -r`. "
            "If specified, this will become proposed replacement text."
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

    # Check for duplicate arguments before parsing
    seen_args = set()
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            arg_name = arg.split("=")[0]
            if arg_name in seen_args:
                parser.error(
                    f"argument {arg_name}: not allowed to be specified multiple times"
                )
            seen_args.add(arg_name)

    args = parser.parse_args()

    global LINTER_NAME, ERROR_DESCRIPTION
    LINTER_NAME = args.linter_name
    ERROR_DESCRIPTION = args.error_description

    logging.basicConfig(
        format="<%(threadName)s:%(levelname)s> %(message)s",
        level=logging.NOTSET
        if args.verbose
        else logging.DEBUG
        if len(args.filenames) < 1000
        else logging.INFO,
        stream=sys.stderr,
    )

    # Filter out files that are too large before running grep
    filtered_filenames = []
    for filename in args.filenames:
        try:
            file_size = os.path.getsize(filename)
            if file_size > MAX_FILE_SIZE:
                print_lint_message(
                    path=filename,
                    severity=LintSeverity.WARNING,
                    name="file-too-large",
                    description=f"File size ({file_size} bytes) exceeds {MAX_FILE_SIZE} bytes limit, skipping",
                )
            else:
                filtered_filenames.append(filename)
        except OSError as err:
            print_lint_message(
                path=filename,
                name="file-access-error",
                description=f"Failed to get file size: {err}",
            )

    # If all files were filtered out, nothing to do
    if not filtered_filenames:
        return

    files_with_matches = []
    if args.match_first_only:
        files_with_matches = ["--files-with-matches"]

    lines = []
    try:
        # Split the grep command into multiple batches to avoid hitting the
        # command line length limit of ~1M on my machine
        arg_length = sum(len(x) for x in filtered_filenames)
        batches = arg_length // 750000 + 1
        batch_size = len(filtered_filenames) // batches
        for i in range(0, len(filtered_filenames), batch_size):
            proc = run_command(
                [
                    "grep",
                    "-nEHI",
                    *files_with_matches,
                    args.pattern,
                    *filtered_filenames[i : i + batch_size],
                ]
            )
            lines.extend(proc.stdout.decode().splitlines())
    except Exception as err:
        print_lint_message(
            name="command-failed",
            description=(
                f"Failed due to {err.__class__.__name__}:\n{err}"
                if not isinstance(err, subprocess.CalledProcessError)
                else (
                    "COMMAND (exit code {returncode})\n"
                    "{command}\n\n"
                    "STDERR\n{stderr}\n\n"
                    "STDOUT\n{stdout}"
                ).format(
                    returncode=err.returncode,
                    command=" ".join(as_posix(x) for x in err.cmd),
                    stderr=err.stderr.decode("utf-8").strip() or "(empty)",
                    stdout=err.stdout.decode("utf-8").strip() or "(empty)",
                )
            ),
        )
        sys.exit(0)

    # Group lines by file to call lint_file once per file
    grouped_lines = group_lines_by_file(lines)

    for filename, line_remainders in grouped_lines.items():
        lint_file(
            filename,
            line_remainders,
            args.allowlist_pattern,
            args.replace_pattern,
            args.error_name,
        )