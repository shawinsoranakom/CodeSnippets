def discover_projects(workspace_pyproject_file: Path) -> List[Path]:
    with workspace_pyproject_file.open("rb") as f:
        data = tomli.load(f)

    projects = data["tool"]["uv"]["workspace"]["members"]
    exclude = data["tool"]["uv"]["workspace"].get("exclude", [])

    all_projects: List[Path] = []
    for project in projects:
        if "*" in project:
            globbed = glob.glob(str(project), root_dir=workspace_pyproject_file.parent)
            globbed_paths = [Path(p) for p in globbed]
            all_projects.extend(globbed_paths)
        else:
            all_projects.append(Path(project))

    for project in exclude:
        if "*" in project:
            globbed = glob.glob(str(project), root_dir=workspace_pyproject_file.parent)
            globbed_paths = [Path(p) for p in globbed]
            all_projects = [p for p in all_projects if p not in globbed_paths]
        else:
            all_projects = [p for p in all_projects if p != Path(project)]

    return all_projects