def check_files(
    filenames: list[str],
    severities: dict[str, LintSeverity],
    *,
    config: str | None,
    retries: int,
    timeout: int,
    explain: bool,
    show_disable: bool,
) -> list[LintMessage]:
    try:
        proc = run_command(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--exit-zero",
                "--quiet",
                "--output-format=json",
                *([f"--config={config}"] if config else []),
                *filenames,
            ],
            retries=retries,
            timeout=timeout,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as err:
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
                    f"Failed due to {err.__class__.__name__}:\n{err}"
                    if not isinstance(err, subprocess.CalledProcessError)
                    else (
                        f"COMMAND (exit code {err.returncode})\n"
                        f"{' '.join(as_posix(x) for x in err.cmd)}\n\n"
                        f"STDERR\n{err.stderr.decode('utf-8').strip() or '(empty)'}\n\n"
                        f"STDOUT\n{err.stdout.decode('utf-8').strip() or '(empty)'}"
                    )
                ),
            )
        ]

    stdout = str(proc.stdout, "utf-8").strip()
    vulnerabilities = json.loads(stdout)

    if explain:
        all_codes = {v["code"] for v in vulnerabilities}
        rules = {code: explain_rule(code) for code in all_codes}
    else:
        rules = {}

    def lint_message(vuln: dict[str, Any]) -> LintMessage:
        code = vuln["code"] or SYNTAX_ERROR
        return LintMessage(
            path=vuln["filename"],
            name=code,
            description=(
                format_lint_message(
                    vuln["message"],
                    code,
                    rules,
                    show_disable and bool(vuln["code"]),
                )
            ),
            line=int(vuln["location"]["row"]),
            char=int(vuln["location"]["column"]),
            code=LINTER_CODE,
            severity=severities.get(code, get_issue_severity(code)),
            original=None,
            replacement=None,
        )

    return [lint_message(v) for v in vulnerabilities]