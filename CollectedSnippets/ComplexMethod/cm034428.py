def install(m, pkgspec, cache, upgrade=False, default_release=None,
            install_recommends=None, force=False,
            dpkg_options=expand_dpkg_options(DPKG_OPTIONS),
            build_dep=False, fixed=False, autoremove=False, fail_on_autoremove=False, only_upgrade=False,
            allow_unauthenticated=False, allow_downgrade=False, allow_change_held_packages=False):
    pkg_list = []
    packages = ""
    pkgspec = expand_pkgspec_from_fnmatches(m, pkgspec, cache)
    package_names = []
    for package in pkgspec:
        if build_dep:
            # Let apt decide what to install
            pkg_list.append("'%s'" % package)
            continue

        name, version_cmp, version = package_split(package)
        package_names.append(name)
        installed, installed_version, version_installable, has_files = package_status(m, name, version_cmp, version, default_release, cache, state='install')

        if not installed and only_upgrade:
            # only_upgrade upgrades packages that are already installed
            # since this package is not installed, skip it
            continue

        if not installed_version and not version_installable:
            status = False
            data = dict(msg="no available installation candidate for %s" % package)
            return (status, data)

        if version_installable and ((not installed and not only_upgrade) or upgrade or not installed_version):
            if version_installable is not True:
                pkg_list.append("'%s=%s'" % (name, version_installable))
            elif version:
                pkg_list.append("'%s=%s'" % (name, version))
            else:
                pkg_list.append("'%s'" % name)
        elif installed_version and version_installable and version_cmp == "=":
            # This happens when the package is installed, a newer version is
            # available, and the version is a wildcard that matches both
            #
            # This is legacy behavior, and isn't documented (in fact it does
            # things documentations says it shouldn't). It should not be relied
            # upon.
            pkg_list.append("'%s=%s'" % (name, version))
    packages = ' '.join(pkg_list)

    if packages:
        if force:
            force_yes = '--force-yes'
        else:
            force_yes = ''

        if m.check_mode:
            check_arg = '--simulate'
        else:
            check_arg = ''

        if autoremove:
            autoremove = '--auto-remove'
        else:
            autoremove = ''

        if fail_on_autoremove:
            fail_on_autoremove = '--no-remove'
        else:
            fail_on_autoremove = ''

        if only_upgrade:
            only_upgrade = '--only-upgrade'
        else:
            only_upgrade = ''

        if fixed:
            fixed = '--fix-broken'
        else:
            fixed = ''

        if build_dep:
            cmd = "%s -y %s %s %s %s %s %s build-dep %s" % (APT_GET_CMD, dpkg_options, only_upgrade, fixed, force_yes, fail_on_autoremove, check_arg, packages)
        else:
            cmd = "%s -y %s %s %s %s %s %s %s install %s" % \
                  (APT_GET_CMD, dpkg_options, only_upgrade, fixed, force_yes, autoremove, fail_on_autoremove, check_arg, packages)

        if default_release:
            cmd += " -t '%s'" % (default_release,)

        if install_recommends is False:
            cmd += " -o APT::Install-Recommends=no"
        elif install_recommends is True:
            cmd += " -o APT::Install-Recommends=yes"
        # install_recommends is None uses the OS default

        if allow_unauthenticated:
            cmd += " --allow-unauthenticated"

        if allow_downgrade:
            cmd += " --allow-downgrades"

        if allow_change_held_packages:
            cmd += " --allow-change-held-packages"

        with PolicyRcD(m):
            rc, out, err = m.run_command(cmd)

        if m._diff:
            diff = parse_diff(out)
        else:
            diff = {}
        status = True

        changed = True
        if build_dep:
            changed = APT_GET_ZERO not in out

        data = dict(changed=changed, stdout=out, stderr=err, diff=diff)
        if rc:
            status = False
            data = dict(msg="'%s' failed: %s" % (cmd, err), stdout=out, stderr=err, rc=rc)
    else:
        status = True
        data = dict(changed=False)

    if not build_dep and not m.check_mode:
        mark_installed(m, package_names, manual=True)

    return (status, data)