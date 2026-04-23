def migrate(
    addons_path: list[str],
    glob: str,
    from_version: tuple[int, ...] | None = None,
    to_version: tuple[int, ...] | None = None,
    script: str | None = None,
    dry_run: bool = False,
):
    if script:
        script_path = next(UPGRADE.glob(f'*{script.removesuffix(".py")}*.py'), None)
        if not script_path:
            raise FileNotFoundError(script)
        script_path.relative_to(UPGRADE)  # safeguard, prevent going up
        module = SourceFileLoader(script_path.name, str(script_path)).load_module()
        modules = [(script_path.name, module)]
    else:
        modules = get_upgrade_code_scripts(from_version, to_version)

    file_manager = FileManager(addons_path, glob)
    for (name, module) in modules:
        file_manager.print_progress(0)  # 0%
        module.upgrade(file_manager)
        file_manager.print_progress(len(file_manager))  # 100%

    for file in file_manager:
        if file.dirty:
            print(file.path)  # noqa: T201
            if not dry_run:
                with file.path.open("w") as f:
                    f.write(file.content)

    return any(file.dirty for file in file_manager)