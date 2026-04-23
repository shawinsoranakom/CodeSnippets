def install(
    *,
    venv: Venv,
    packages: Iterable[str],
    subcommand: str = "checkout",
    branch: str | None = None,
    fresh_venv: bool = False,
    assume_yes: bool = False,
) -> None:
    """Development install of PyTorch"""
    if not fresh_venv:
        print(f"Using existing venv: {venv.prefix}")
        venv.ensure()
    else:
        venv.create(remove_if_exists=True, assume_yes=assume_yes)

    packages = [p for p in packages if p != "torch"]

    downloaded_files = venv.pip_download("torch", prerelease=True, no_deps=True)
    if len(downloaded_files) != 1:
        raise RuntimeError(f"Expected exactly one torch wheel, got {downloaded_files}")
    torch_wheel = downloaded_files[0]
    if not (
        torch_wheel.name.startswith("torch-") and torch_wheel.name.endswith(".whl")
    ):
        raise RuntimeError(f"Expected exactly one torch wheel, got {torch_wheel}")

    with venv.extracted_wheel(torch_wheel) as wheel_site_dir:
        dependencies = parse_dependencies(venv, wheel_site_dir)
        install_packages(venv, [*dependencies, *packages])

        if subcommand == "checkout":
            checkout_nightly_version(branch, wheel_site_dir)
        elif subcommand == "pull":
            pull_nightly_version(wheel_site_dir)
        else:
            raise ValueError(f"Subcommand {subcommand} must be one of: checkout, pull.")
        move_nightly_files(wheel_site_dir)

    write_pth(venv)
    cast(logging.Logger, LOGGER).info(
        "-------\n"
        "PyTorch Development Environment set up!\n"
        "Please activate to enable this environment:\n\n"
        "  $ %s\n",
        venv.activate_command,
    )