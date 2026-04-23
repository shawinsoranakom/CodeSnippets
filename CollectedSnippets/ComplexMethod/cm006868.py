def _render_result(
    result: ValidationResult,
    *,
    index: int,
    total: int,
    verbose: bool,
    strict: bool = False,
) -> None:
    counter = f"[dim][{index}/{total}][/dim] " if total > 1 else ""
    label = f"[bold]{result.path}[/bold]"
    passes = result.ok and not (strict and result.warnings)
    if passes:
        ok_console.print(f"{counter}[green]\u2713[/green] {label}")
    else:
        console.print(f"{counter}[red]\u2717[/red] {label}")

    show_issues = verbose or not passes
    if show_issues:
        for issue in result.issues:
            effective_severity = "error" if (strict and issue.severity == "warning") else issue.severity
            color = "red" if effective_severity == "error" else "yellow"
            loc = f" [{issue.node_name or issue.node_id}]" if (issue.node_id or issue.node_name) else ""
            console.print(f"  [{color}][L{issue.level} {effective_severity.upper()}][/{color}]{loc} {issue.message}")