def init_command(
    project_dir: Path,
    *,
    github_actions: bool,
    overwrite: bool,
    example: bool = True,
) -> None:
    """Scaffold a Flow DevOps project at *project_dir*."""
    target = project_dir.resolve()

    if target.exists() and not overwrite:
        existing = [p for p in target.iterdir() if p.name != ".git"]
        if existing:
            msg = f"{target} already exists and is not empty. Use [bold]--overwrite[/bold] to scaffold into it anyway."
            console.print(f"[red]Error:[/red] {msg}")
            raise typer.Exit(1)

    target.mkdir(parents=True, exist_ok=True)
    created: list[tuple[str, str]] = []

    kw: dict[str, Any] = {"target": target, "overwrite": overwrite, "created": created}

    # flows/
    (target / "flows").mkdir(exist_ok=True)
    if example:
        from lfx.cli.create import create_command as _create

        try:
            _create(
                "hello-world",
                template="hello-world",
                output_dir=target / "flows",
                overwrite=overwrite,
            )
            created.append(("flows/hello-world.json", "starter flow — edit or replace"))
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            # Don't let a template failure block the rest of init
            console.print(f"[yellow]Warning:[/yellow] Could not seed starter flow: {exc}")
    else:
        _write(target / "flows" / ".gitkeep", "", "versioned empty directory", **kw)

    # tests/
    _write(target / "tests" / "__init__.py", "", "", **kw)
    _write(target / "tests" / "test_flows.py", _TEST_FLOWS_PY, "flow_runner example tests", **kw)

    # .lfx/environments.yaml
    _write(
        target / ".lfx" / "environments.yaml",
        _ENVIRONMENTS_YAML,
        "edit with your instance URLs + API key env var names (safe to commit)",
        **kw,
    )

    # .gitignore — keep langflow-environments.toml ignored for backward compat
    gitignore = target / ".gitignore"
    if gitignore.exists():
        existing_content = gitignore.read_text(encoding="utf-8")
        if "langflow-environments.toml" not in existing_content:
            gitignore.write_text(existing_content.rstrip() + "\n\n" + _GITIGNORE, encoding="utf-8")
            created.append((".gitignore", "appended credentials ignore rule"))
    else:
        _write(gitignore, _GITIGNORE, "ignores legacy credentials file", **kw)

    # GitHub Actions CI workflows
    if github_actions:
        gha_src = _TEMPLATES_DIR / "github-actions"
        if gha_src.exists():
            for tmpl in sorted(gha_src.glob("*.yml")):
                dest = target / ".github" / "workflows" / tmpl.name
                _copy_template(tmpl, dest, "CI workflow", created, target=target, overwrite=overwrite)
        else:
            console.print("[yellow]Warning:[/yellow] GitHub Actions templates not found; skipping.")

    # Generic shell CI scripts (always scaffolded — work with any CI system)
    shell_src = _TEMPLATES_DIR / "shell"
    if shell_src.exists():
        for tmpl in sorted(shell_src.glob("*.sh")):
            dest = target / "ci" / tmpl.name
            _copy_template(tmpl, dest, "generic CI script", created, target=target, overwrite=overwrite)
            dest.chmod(dest.stat().st_mode | 0o111)  # ensure executable bit

    # Print the created-files tree
    _render_tree(target, created)

    # Next-steps guide
    console.print()
    console.print("[bold green]✓ Project scaffolded.[/bold green]  Next steps:\n")
    console.print("  1. Edit [bold].lfx/environments.yaml[/bold] with your instance URL")
    console.print("  2. [bold]export LANGFLOW_LOCAL_API_KEY=<key>[/bold]   (Settings → API Keys)")
    if example:
        console.print("  3. [bold]lfx validate flows/hello-world.json[/bold]  (check the starter flow)")
        console.print("  4. [bold]lfx serve flows/hello-world.json[/bold]     (run it locally)")
        console.print("  5. [bold]lfx push --dir flows/ --env local[/bold]    (deploy to Langflow)")
    else:
        console.print("  3. [bold]lfx create my-flow --template hello-world[/bold]")
        console.print("  4. [bold]lfx push --dir flows/ --env local[/bold]")
    console.print(f"  {'6' if example else '5'}. [bold]pytest tests/ --langflow-env local[/bold]")
    console.print()