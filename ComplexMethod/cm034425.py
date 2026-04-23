def package_best_match(pkgname, version_cmp, version, release, cache):
    policy = apt_pkg.Policy(cache)

    policy.read_pinfile(apt_pkg.config.find_file("Dir::Etc::preferences"))
    policy.read_pindir(apt_pkg.config.find_file("Dir::Etc::preferencesparts"))

    if release:
        # 990 is the priority used in `apt-get -t`
        policy.create_pin('Release', pkgname, release, 990)
    if version_cmp == "=":
        # Installing a specific version from command line overrides all pinning
        # We don't mimic this exactly, but instead set a priority which is higher than all APT built-in pin priorities.
        policy.create_pin('Version', pkgname, version, 1001)
    pkg = cache[pkgname]
    pkgver = policy.get_candidate_ver(pkg)
    if not pkgver:
        return None
    # Check if the available version matches the requested version
    if version_cmp == "=" and not fnmatch.fnmatch(pkgver.ver_str, version):
        # Even though we put in a pin policy, it can be ignored if there is no
        # possible candidate.
        return None
    if version_cmp == ">=" and not apt_pkg.version_compare(pkgver.ver_str, version) >= 0:
        return None
    return pkgver.ver_str