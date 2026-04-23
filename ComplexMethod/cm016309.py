def check_files(
    code: str, config: str, remove_unused_ignores: bool, suppress: bool
) -> list[LintMessage]:
    try:
        pyrefly_commands = [
            "pyrefly",
            "check",
            "--config",
            config,
            "--output-format=json",
        ]
        if remove_unused_ignores:
            pyrefly_commands.append("--remove-unused-ignores")
        if suppress:
            pyrefly_commands.append("--suppress-errors")
        proc = run_command(
            [*pyrefly_commands],
            extra_env={},
            retries=0,
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

    # Parse JSON output from pyrefly. In GitHub Actions, pyrefly appends
    # ::error commands to stdout after the JSON, so use raw_decode to parse
    # only the first JSON object and ignore trailing output.
    try:
        if stdout:
            result, _ = json.JSONDecoder().raw_decode(stdout)
            errors = result.get("errors", [])
        else:
            errors = []
        errors = [error for error in errors if error["name"] != "deprecated"]
        rc = [
            LintMessage(
                path=error["path"],
                name=error["name"],
                description=error.get(
                    "description", error.get("concise_description", "")
                ),
                line=error["line"],
                char=error["column"],
                code=code,
                severity=LintSeverity.ADVICE
                if error["name"] == "deprecated"
                else LintSeverity.ERROR,
                original=None,
                replacement=None,
            )
            for error in errors
        ]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return [
            LintMessage(
                path=None,
                line=None,
                char=None,
                code=code,
                severity=LintSeverity.ERROR,
                name="json-parse-error",
                original=None,
                replacement=None,
                description=f"Failed to parse pyrefly JSON output: {e}",
            )
        ]

    # Still check stderr for internal errors
    rc += [
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