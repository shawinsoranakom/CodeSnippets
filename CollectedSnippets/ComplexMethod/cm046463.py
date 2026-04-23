def copy_globs(
    source_dir: Path, destination: Path, patterns: list[str], *, required: bool = True
) -> None:
    destination.mkdir(parents = True, exist_ok = True)
    matched_sources: dict[str, Path] = {}
    for path in sorted(
        (candidate for candidate in source_dir.rglob("*") if candidate.is_file()),
        key = lambda candidate: (
            len(candidate.relative_to(source_dir).parts),
            str(candidate),
        ),
    ):
        for pattern in patterns:
            if fnmatch.fnmatch(path.name, pattern):
                previous = matched_sources.get(path.name)
                if previous is not None and previous != path:
                    raise PrebuiltFallback(
                        f"ambiguous archive layout for {path.name}: "
                        f"{previous.relative_to(source_dir)} and {path.relative_to(source_dir)}"
                    )
                matched_sources[path.name] = path
                break

    if required and not matched_sources:
        raise PrebuiltFallback(f"required files missing from {source_dir}: {patterns}")

    for name, path in matched_sources.items():
        shutil.copy2(path, destination / name)