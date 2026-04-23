def _is_newer_version_installed(base, pkg_spec):
    """Check if a newer version of the package is already installed."""
    try:
        if isinstance(pkg_spec, dnf.package.Package):
            installed = sorted(base.sack.query().installed().filter(name=pkg_spec.name, arch=pkg_spec.arch))[-1]
            return installed.evr_gt(pkg_spec)
        else:
            solution = dnf.subject.Subject(pkg_spec).get_best_solution(base.sack)
            q = solution['query']
            nevra = solution['nevra']
            if not q or not nevra or nevra.has_just_name() or not nevra.version:
                return False

            # Filter by name and arch (if specified), but NOT by version
            # since we need to find installed packages to compare versions against
            filter_kwargs = {'name': nevra.name}
            if nevra.arch:
                filter_kwargs['arch'] = nevra.arch
            installed = base.sack.query().installed().filter(**filter_kwargs)
            if not installed:
                return False
            return installed[0].evr_gt(q[0])
    except IndexError:
        return False