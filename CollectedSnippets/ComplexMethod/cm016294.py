def check_files(
    filenames: list[str],
    config: str,
    retries: int,
    code: str,
) -> list[LintMessage]:
    # dmypy has a bug where it won't pick up changes if you pass it absolute
    # file names, see https://github.com/python/mypy/issues/16768
    filenames = [os.path.relpath(f) for f in filenames]
    try:
        mypy_commands = ["dmypy", "run", "--"]
        if in_github_actions():
            mypy_commands = ["mypy"]
        proc = run_command(
            [*mypy_commands, f"--config={config}"] + filenames,
            extra_env={},
            retries=retries,
        )
    except OSError as err:
        return [
            LintMessage(
                path=None,
                line=None,
                char=None,
                code=code,
                severity=LintSeverity.ERROR,
                name="command-failed",
                original=None,
                replacement=None,
                description=(f"Failed due to {err.__class__.__name__}:\n{err}"),
            )
        ]
    stdout = str(proc.stdout, "utf-8").strip()
    stderr = str(proc.stderr, "utf-8").strip()
    if proc.returncode not in (0, 1):
        return [
            LintMessage(
                path=None,
                line=None,
                char=None,
                code=code,
                severity=LintSeverity.ERROR,
                name="command-failed",
                original=None,
                replacement=None,
                description=stderr,
            )
        ]

    rc = [
        LintMessage(
            path=match["file"],
            name=match["code"],
            description=match["message"],
            line=int(match["line"]),
            char=int(match["column"])
            if match["column"] is not None and not match["column"].startswith("-")
            else None,
            code=code,
            severity=severities.get(match["severity"], LintSeverity.ERROR),
            original=None,
            replacement=None,
        )
        for match in RESULTS_RE.finditer(stdout)
    ] + [
        LintMessage(
            path=match["file"],
            name="INTERNAL ERROR",
            description=match["message"],
            line=int(match["line"]),
            char=None,
            code=code,
            severity=severities.get(match["severity"], LintSeverity.ERROR),
            original=None,
            replacement=None,
        )
        for match in INTERNAL_ERROR_RE.finditer(stderr)
    ]
    return rc