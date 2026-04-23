def expand_pkgspec_from_fnmatches(m, pkgspec, cache):
    # Note: apt-get does implicit regex matching when an exact package name
    # match is not found.  Something like this:
    # matches = [pkg.name for pkg in cache if re.match(pkgspec, pkg.name)]
    # (Should also deal with the ':' for multiarch like the fnmatch code below)
    #
    # We have decided not to do similar implicit regex matching but might take
    # a PR to add some sort of explicit regex matching:
    # https://github.com/ansible/ansible-modules-core/issues/1258
    new_pkgspec = []
    if pkgspec:
        for pkgspec_pattern in pkgspec:

            if not isinstance(pkgspec_pattern, str):
                m.fail_json(msg="Invalid type for package name, expected string but got %s" % type(pkgspec_pattern))

            pkgname_pattern, version_cmp, version = package_split(pkgspec_pattern)

            # note that none of these chars is allowed in a (debian) pkgname
            if frozenset('*?[]!').intersection(pkgname_pattern):
                # handle multiarch pkgnames, the idea is that "apt*" should
                # only select native packages. But "apt*:i386" should still work
                if ":" not in pkgname_pattern:
                    # Filter the multiarch packages from the cache only once
                    try:
                        pkg_name_cache = _non_multiarch  # pylint: disable=used-before-assignment
                    except NameError:
                        pkg_name_cache = _non_multiarch = [pkg.name for pkg in cache if ':' not in pkg.name]  # noqa: F841
                else:
                    # Create a cache of pkg_names including multiarch only once
                    try:
                        pkg_name_cache = _all_pkg_names  # pylint: disable=used-before-assignment
                    except NameError:
                        pkg_name_cache = _all_pkg_names = [pkg.name for pkg in cache]  # noqa: F841

                matches = fnmatch.filter(pkg_name_cache, pkgname_pattern)

                if not matches:
                    m.fail_json(msg="No package(s) matching '%s' available" % to_text(pkgname_pattern))
                else:
                    new_pkgspec.extend(matches)
            else:
                # No wildcards in name
                new_pkgspec.append(pkgspec_pattern)
    return new_pkgspec