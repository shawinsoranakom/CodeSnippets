def install_recommended_packages(cache: apt.Cache, recommended_packages: str) -> list[str]:
    deps_to_install = []
    for recommend_one_of in apt_pkg.parse_depends(recommended_packages, False):
        for name, version, op in recommend_one_of:
            try:
                pkg = cache[name]
            except KeyError:
                # no package found, continue with next recommended package
                continue

            if pkg.is_installed and version and op and apt_pkg.check_dep(pkg.installed.version, op, version):
                # package is installed and the version is the same, continue with next recommended package
                break

            if not pkg.candidate:
                # no candidate found, continue with next recommended package
                continue

            if version and op and not apt_pkg.check_dep(pkg.candidate.version, op, version):
                # candidate version does not match the version, continue with next recommended package
                continue

            deps_to_install.append(name)
            break
    return deps_to_install