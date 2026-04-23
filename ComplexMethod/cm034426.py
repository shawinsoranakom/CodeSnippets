def package_status(m, pkgname, version_cmp, version, default_release, cache, state):
    """
    :return: A tuple of (installed, installed_version, version_installable, has_files). *installed* indicates whether
    the package (regardless of version) is installed. *installed_version* indicates whether the installed package
    matches the provided version criteria. *version_installable* provides the latest matching version that can be
    installed. In the case of virtual packages where we can't determine an applicable match, True is returned.
    *has_files* indicates whether the package has files on the filesystem (even if not installed, meaning a purge is
    required).
    """
    try:
        # get the package from the cache, as well as the
        # low-level apt_pkg.Package object which contains
        # state fields not directly accessible from the
        # higher-level apt.package.Package object.
        pkg = cache[pkgname]
        ll_pkg = cache._cache[pkgname]  # the low-level package object
    except KeyError:
        if state == 'install':
            try:
                provided_packages = cache.get_providing_packages(pkgname)
                if provided_packages:
                    # When this is a virtual package satisfied by only
                    # one installed package, return the status of the target
                    # package to avoid requesting re-install
                    if cache.is_virtual_package(pkgname) and len(provided_packages) == 1:
                        package = provided_packages[0]
                        installed, installed_version, version_installable, has_files = \
                            package_status(m, package.name, version_cmp, version, default_release, cache, state='install')
                        if installed:
                            return installed, installed_version, version_installable, has_files

                    # Otherwise return nothing so apt will sort out
                    # what package to satisfy this with
                    return False, False, True, False

                m.fail_json(msg="No package matching '%s' is available" % pkgname)
            except AttributeError:
                # python-apt version too old to detect virtual packages
                # mark as not installed and let apt-get install deal with it
                return False, False, True, False
        else:
            return False, False, None, False
    try:
        has_files = len(pkg.installed_files) > 0
    except UnicodeDecodeError:
        has_files = True
    except AttributeError:
        has_files = False  # older python-apt cannot be used to determine non-purged

    try:
        package_is_installed = ll_pkg.current_state == apt_pkg.CURSTATE_INSTALLED
    except AttributeError:  # python-apt 0.7.X has very weak low-level object
        try:
            # might not be necessary as python-apt post-0.7.X should have current_state property
            package_is_installed = pkg.is_installed
        except AttributeError:
            # assume older version of python-apt is installed
            package_is_installed = pkg.isInstalled

    version_best = package_best_match(pkgname, version_cmp, version, default_release, cache._cache)
    version_is_installed = False
    version_installable = None
    if package_is_installed:
        try:
            installed_version = pkg.installed.version
        except AttributeError:
            installed_version = pkg.installedVersion

        # Check if the installed version already matches the requested version
        if version_cmp == "=":
            version_is_installed = fnmatch.fnmatch(installed_version, version)
        elif version_cmp == ">=":
            version_is_installed = apt_pkg.version_compare(installed_version, version) >= 0
        else:
            version_is_installed = True

        # Check if a better version is available
        if version_best and installed_version != version_best:
            version_installable = version_best
    else:
        version_installable = version_best

    return package_is_installed, version_is_installed, version_installable, has_files