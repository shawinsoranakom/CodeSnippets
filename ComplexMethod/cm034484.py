def _resolve_package_names(
        module: AnsibleModule,
        package_list: list[Package],
        pip: list[str],
        python_bin: str,
) -> list[Package]:
    """Resolve package references in the list.

    This helper function downloads metadata from PyPI
    using ``pip install``'s ability to return JSON.
    """
    pkgs_to_resolve = [pkg for pkg in package_list if not pkg.has_requirement]

    if not pkgs_to_resolve:
        return package_list

    # pip install --dry-run is not available in pip versions older than 22.2 and it doesn't
    # work correctly on all cases until 24.1, so check for this and use the non-resolved
    # package names if pip is outdated.
    pip_dep = _get_package_info(module, "pip", python_bin)

    installed_pip = LooseVersion(pip_dep.split('==')[1])
    minimum_pip = LooseVersion("24.1")

    if installed_pip < minimum_pip:
        module.warn("Using check mode with packages from vcs urls, file paths, or archives will not behave as expected when using pip versions <24.1.")
        return package_list  # Just use the default behavior

    with tempfile.NamedTemporaryFile() as tmpfile:
        # Uses a tmpfile instead of capturing and parsing stdout because it circumvents the need to fuss with ANSI color output
        module.run_command(
            [
                *pip, 'install',
                '--dry-run',
                '--ignore-installed',
                f'--report={tmpfile.name}',
                *map(str, pkgs_to_resolve),
            ],
            check_rc=True,
        )
        report = json.load(tmpfile)

    package_objects = (
        Package(install_report['metadata']['name'], version_string=install_report['metadata']['version'])
        for install_report in report['install']
    )

    other_packages = (pkg for pkg in package_list if pkg.has_requirement)
    return [*other_packages, *package_objects]