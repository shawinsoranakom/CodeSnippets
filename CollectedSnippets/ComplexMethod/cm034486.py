def is_newer_version_installed(base, spec):
    # expects a versioned package spec
    if "/" in spec:
        spec = spec.split("/")[-1]
        if spec.endswith(".rpm"):
            spec = spec[:-4]

    settings = get_resolve_spec_settings()
    match, spec_nevra = libdnf5.rpm.PackageQuery(base).resolve_pkg_spec(spec, settings, True)
    if not match or spec_nevra.has_just_name():
        return False
    spec_name = spec_nevra.get_name()

    installed = libdnf5.rpm.PackageQuery(base)
    installed.filter_installed()
    installed.filter_name([spec_name])
    installed.filter_latest_evr()
    try:
        installed_package = list(installed)[-1]
    except IndexError:
        return False

    target = libdnf5.rpm.PackageQuery(base)
    target.filter_name([spec_name])
    target.filter_version([spec_nevra.get_version()])
    spec_release = spec_nevra.get_release()
    if spec_release:
        target.filter_release([spec_release])
    spec_epoch = spec_nevra.get_epoch()
    if spec_epoch:
        target.filter_epoch([spec_epoch])
    target.filter_latest_evr()
    try:
        target_package = list(target)[-1]
    except IndexError:
        return False

    # FIXME https://github.com/rpm-software-management/dnf5/issues/1104
    return libdnf5.rpm.rpmvercmp(installed_package.get_evr(), target_package.get_evr()) == 1