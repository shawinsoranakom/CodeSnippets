def check_files(
    filenames: list[str],
    flake8_plugins_path: str | None,
    severities: dict[str, LintSeverity],
    retries: int,
) -> list[LintMessage]:
    try:
        proc = run_command(
            [sys.executable, "-mflake8", "--exit-zero"] + filenames,
            extra_env={"FLAKE8_PLUGINS_PATH": flake8_plugins_path}
            if flake8_plugins_path
            else None,
            retries=retries,
        )
    except (OSError, subprocess.CalledProcessError) as err:
        return [
            LintMessage(
                path=None,
                line=None,
                char=None,
                code="FLAKE8",
                severity=LintSeverity.ERROR,
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
                        stderr=err.stderr.strip() or "(empty)",
                        stdout=err.stdout.strip() or "(empty)",
                    )
                ),
            )
        ]

    return [
        LintMessage(
            path=match["file"],
            name=match["code"],
            description=f"{match['message']}\nSee {get_issue_documentation_url(match['code'])}",
            line=int(match["line"]),
            char=int(match["column"])
            if match["column"] is not None and not match["column"].startswith("-")
            else None,
            code="FLAKE8",
            severity=severities.get(match["code"]) or get_issue_severity(match["code"]),
            original=None,
            replacement=None,
        )
        for match in RESULTS_RE.finditer(proc.stdout)
    ]