def check_files(
    files: list[str],
) -> list[LintMessage]:
    args = ["--external-sources", "--format=json1"] + files

    proc: subprocess.CompletedProcess[bytes] | None = None
    last_error: OSError | None = None

    for shellcheck in _shellcheck_candidates():
        try:
            proc = run_command([shellcheck] + args)
            break
        except OSError as err:
            last_error = err

    if proc is None:
        if last_error is not None and last_error.errno == 8:
            return []
        if not _is_x86_64():
            return []
        return [
            LintMessage(
                path=None,
                line=None,
                char=None,
                code=LINTER_CODE,
                severity=LintSeverity.ERROR,
                name="command-failed",
                original=None,
                replacement=None,
                description=(
                    f"Failed to execute shellcheck.\n{last_error.__class__.__name__}: {last_error}"
                    if last_error is not None
                    else "Failed to find a usable shellcheck executable."
                ),
            )
        ]
    stdout = str(proc.stdout, "utf-8").strip()
    results = json.loads(stdout)["comments"]
    return [
        LintMessage(
            path=result["file"],
            name=f"SC{result['code']}",
            description=result["message"],
            line=result["line"],
            char=result["column"],
            code=LINTER_CODE,
            severity=LintSeverity.ERROR,
            original=None,
            replacement=None,
        )
        for result in results
    ]