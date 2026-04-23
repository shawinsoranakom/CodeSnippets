def lint_file(
    filename: str,
    line_remainders: list[str],
    allowlist_pattern: str,
    replace_pattern: str,
    error_name: str,
) -> None:
    """
    Lint a file with one or more pattern matches, printing LintMessages as they're created.

    Args:
        filename: Path to the file being linted
        line_remainders: List of line remainders (format: "line:content" without filename prefix)
        allowlist_pattern: Pattern to check for allowlisting
        replace_pattern: Pattern for sed replacement
        error_name: Human-readable error name
    """
    if not line_remainders:
        return

    should_skip = check_allowlist(filename, allowlist_pattern)
    if should_skip:
        return

    # Check if file is too large to compute replacement
    file_size = os.path.getsize(filename)
    compute_replacement = replace_pattern and file_size <= MAX_ORIGINAL_SIZE

    # Apply replacement to entire file if pattern is specified and file is not too large
    original = None
    replacement = None
    if compute_replacement:
        # When we have a replacement, report a single message with line=None
        try:
            with open(filename) as f:
                original = f.read()

            proc = run_command(["sed", "-r", replace_pattern, filename])
            replacement = proc.stdout.decode("utf-8")
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
            return

        print_lint_message(
            path=filename,
            name=error_name,
            original=original,
            replacement=replacement,
        )
    else:
        # When no replacement, report each matching line (up to MAX_MATCHES_PER_FILE)
        total_matches = len(line_remainders)
        matches_to_report = min(total_matches, MAX_MATCHES_PER_FILE)

        for line_remainder in line_remainders[:matches_to_report]:
            # line_remainder format: "line_number:content"
            split = line_remainder.split(":", 1)
            line_number = int(split[0]) if split[0] else None
            print_lint_message(
                path=filename,
                line=line_number,
                name=error_name,
            )

        # If there are more matches than the limit, print an error
        if total_matches > MAX_MATCHES_PER_FILE:
            print_lint_message(
                path=filename,
                name="too-many-matches",
                description=f"File has {total_matches} matches, only showing first {MAX_MATCHES_PER_FILE}",
            )