def _install_shared_infra(
    project_path: Path,
    script_type: str,
    tracker: StepTracker | None = None,
    force: bool = False,
) -> bool:
    """Install shared infrastructure files into *project_path*.

    Copies ``.specify/scripts/`` and ``.specify/templates/`` from the
    bundled core_pack or source checkout.  Tracks all installed files
    in ``speckit.manifest.json``.

    When *force* is ``True``, existing files are overwritten with the
    latest bundled versions.  When ``False`` (default), only missing
    files are added and existing ones are skipped.

    Returns ``True`` on success.
    """
    from .integrations.manifest import IntegrationManifest

    core = _locate_core_pack()
    manifest = IntegrationManifest("speckit", project_path, version=get_speckit_version())

    # Scripts
    if core and (core / "scripts").is_dir():
        scripts_src = core / "scripts"
    else:
        repo_root = Path(__file__).parent.parent.parent
        scripts_src = repo_root / "scripts"

    skipped_files: list[str] = []

    if scripts_src.is_dir():
        dest_scripts = project_path / ".specify" / "scripts"
        dest_scripts.mkdir(parents=True, exist_ok=True)
        variant_dir = "bash" if script_type == "sh" else "powershell"
        variant_src = scripts_src / variant_dir
        if variant_src.is_dir():
            dest_variant = dest_scripts / variant_dir
            dest_variant.mkdir(parents=True, exist_ok=True)
            for src_path in variant_src.rglob("*"):
                if src_path.is_file():
                    rel_path = src_path.relative_to(variant_src)
                    dst_path = dest_variant / rel_path
                    if dst_path.exists() and not force:
                        skipped_files.append(str(dst_path.relative_to(project_path)))
                    else:
                        dst_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_path, dst_path)
                        rel = dst_path.relative_to(project_path).as_posix()
                        manifest.record_existing(rel)

    # Page templates (not command templates, not vscode-settings.json)
    if core and (core / "templates").is_dir():
        templates_src = core / "templates"
    else:
        repo_root = Path(__file__).parent.parent.parent
        templates_src = repo_root / "templates"

    if templates_src.is_dir():
        dest_templates = project_path / ".specify" / "templates"
        dest_templates.mkdir(parents=True, exist_ok=True)
        for f in templates_src.iterdir():
            if f.is_file() and f.name != "vscode-settings.json" and not f.name.startswith("."):
                dst = dest_templates / f.name
                if dst.exists() and not force:
                    skipped_files.append(str(dst.relative_to(project_path)))
                else:
                    shutil.copy2(f, dst)
                    rel = dst.relative_to(project_path).as_posix()
                    manifest.record_existing(rel)

    if skipped_files:
        console.print(
            f"[yellow]⚠[/yellow]  {len(skipped_files)} shared infrastructure file(s) already exist and were not updated:"
        )
        for f in skipped_files:
            console.print(f"    {f}")
        console.print(
            "To refresh shared infrastructure, run "
            "[cyan]specify init --here --force[/cyan] or "
            "[cyan]specify integration upgrade --force[/cyan]."
        )

    manifest.save()
    return True