def check_file(
    filename: str,
    binary: str,
    retries: int,
    timeout: int,
) -> list[LintMessage]:
    try:
        with open(filename, "rb") as f:
            original = f.read()
        proc = run_command(
            [binary, filename],
            retries=retries,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return [
            LintMessage(
                path=filename,
                line=None,
                char=None,
                code="CLANGFORMAT",
                severity=LintSeverity.ERROR,
                name="timeout",
                original=None,
                replacement=None,
                description=(
                    "clang-format timed out while trying to process a file. "
                    "Please report an issue in pytorch/pytorch with the "
                    "label 'module: lint'"
                ),
            )
        ]
    except (OSError, subprocess.CalledProcessError) as err:
        return [
            LintMessage(
                path=filename,
                line=None,
                char=None,
                code="CLANGFORMAT",
                severity=LintSeverity.ADVICE,
                name="command-failed",
                original=None,
                replacement=None,
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
        ]

    replacement = proc.stdout
    if original == replacement:
        return []

    return [
        LintMessage(
            path=filename,
            line=None,
            char=None,
            code="CLANGFORMAT",
            severity=LintSeverity.WARNING,
            name="format",
            original=original.decode("utf-8"),
            replacement=replacement.decode("utf-8"),
            description="See https://clang.llvm.org/docs/ClangFormat.html.\nRun `lintrunner -a` to apply this patch.",
        )
    ]