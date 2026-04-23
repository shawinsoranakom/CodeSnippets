def validate_command(
    flow_paths: list[str],
    level: int,
    *,
    skip_components: bool,
    skip_edge_types: bool,
    skip_required_inputs: bool,
    skip_version_check: bool,
    skip_credentials: bool,
    strict: bool,
    verbose: bool,
    output_format: str,
) -> None:
    if not flow_paths:
        flow_paths = [_DEFAULT_FLOWS_DIR]

    paths = _expand_paths(flow_paths)

    if not paths:
        console.print("[yellow]No flow files to validate.[/yellow]")
        raise typer.Exit(0)

    results: list[ValidationResult] = []
    for i, p in enumerate(paths, start=1):
        result = validate_flow_file(
            p,
            level=level,
            skip_components=skip_components,
            skip_edge_types=skip_edge_types,
            skip_required_inputs=skip_required_inputs,
            skip_version_check=skip_version_check,
            skip_credentials=skip_credentials,
        )
        results.append(result)
        if output_format != "json":
            _render_result(result, index=i, total=len(paths), verbose=verbose, strict=strict)

    if output_format == "json":
        import json as _json

        out = [
            {
                "path": str(r.path),
                "ok": r.ok if not strict else (not r.errors and not r.warnings),
                "issues": [
                    {
                        "level": i.level,
                        "severity": i.severity,
                        "node_id": i.node_id,
                        "node_name": i.node_name,
                        "message": i.message,
                    }
                    for i in r.issues
                ],
            }
            for r in results
        ]
        sys.stdout.write(_json.dumps(out, indent=2) + "\n")
    elif len(paths) > 1:
        passed = sum(1 for r in results if r.ok and not (strict and r.warnings))
        failed = len(results) - passed
        color = "green" if failed == 0 else "red"
        ok_console.print(f"\n[{color}]Validated {len(paths)} flows: {passed} passed, {failed} failed.[/{color}]")

    if any((not r.ok) or (strict and r.warnings) for r in results):
        raise typer.Exit(1)