def check_licenses(args: CheckArgs) -> int:
    """Check licenses are OSI approved."""
    exit_code = 0
    raw_licenses = json.loads(Path(args.path).read_text())
    license_status = {
        pkg.name: (pkg, check_license_status(pkg))
        for data in raw_licenses
        if (pkg := PackageDefinition.from_dict(data))
    }

    for name, version in TODO.items():
        pkg, status = license_status.get(name, (None, None))
        if pkg is None or not (version < pkg.version):
            continue
        assert status is not None

        if status is True:
            print(
                "Approved license detected for "
                f"{pkg.name}@{pkg.version}: {get_license_str(pkg)}\n"
                "Please remove the package from the TODO list.\n"
            )
        else:
            print(
                "We could not detect an OSI-approved license for "
                f"{pkg.name}@{pkg.version}: {get_license_str(pkg)}\n"
                "Please update the package version on the TODO list.\n"
            )
        exit_code = 1

    for pkg, status in license_status.values():
        if status is False and pkg.name not in EXCEPTIONS_AND_TODOS:
            print(
                "We could not detect an OSI-approved license for "
                f"{pkg.name}@{pkg.version}: {get_license_str(pkg)}\n"
            )
            exit_code = 1
        if status is True and pkg.name in EXCEPTIONS:
            print(
                "Approved license detected for "
                f"{pkg.name}@{pkg.version}: {get_license_str(pkg)}\n"
                "Please remove the package from the EXCEPTIONS list.\n"
            )
            exit_code = 1

    for name in EXCEPTIONS_AND_TODOS.difference(license_status):
        print(
            f"Package {name} is tracked, but not used. "
            "Please remove it from the licenses.py file.\n"
        )
        exit_code = 1

    return exit_code