def check_allowlist(
    filename: str,
    allowlist_pattern: str,
) -> bool:
    """
    Check if a file matches the allowlist pattern.

    Args:
        filename: Path to the file to check
        allowlist_pattern: Pattern to grep for in the file

    Returns:
        True if the file should be skipped (allowlist pattern matched), False otherwise.
        Prints error message and returns False if there was an error running grep.
    """
    if not allowlist_pattern:
        return False

    try:
        proc = run_command(["grep", "-nEHI", allowlist_pattern, filename])
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
        return False

    # allowlist pattern was found, abort lint
    if proc.returncode == 0:
        return True

    return False