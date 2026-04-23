def _get_package_dirs() -> set[str]:
    libs = REPO_ROOT / "libs"
    dirs: set[str] = set()
    # Top-level packages (libs/core, libs/langchain, etc.)
    for p in libs.iterdir():
        if p.is_dir() and (p / "pyproject.toml").exists():
            dirs.add(f"libs/{p.name}")
    # Partner packages (libs/partners/*)
    partners = libs / "partners"
    if partners.exists():
        for p in partners.iterdir():
            if p.is_dir() and (p / "pyproject.toml").exists():
                dirs.add(f"libs/partners/{p.name}")
    return dirs