def install_deb(
        m, debs, cache, force, fail_on_autoremove, install_recommends,
        allow_unauthenticated,
        allow_downgrade,
        allow_change_held_packages,
        dpkg_options,
        lock_timeout,
):
    changed = False
    deps_to_install = []
    pkgs_to_install = []
    for deb_file in debs.split(','):
        try:
            pkg = apt.debfile.DebPackage(deb_file, cache=apt.Cache())
            pkg_name = get_field_of_deb(m, deb_file, "Package")
            pkg_version = get_field_of_deb(m, deb_file, "Version")
            if hasattr(apt_pkg, 'get_architectures') and len(apt_pkg.get_architectures()) > 1:
                pkg_arch = get_field_of_deb(m, deb_file, "Architecture")
                pkg_key = "%s:%s" % (pkg_name, pkg_arch)
            else:
                pkg_key = pkg_name
            try:
                installed_pkg = apt.Cache()[pkg_key]
                installed_version = installed_pkg.installed.version
                if package_version_compare(pkg_version, installed_version) == 0:
                    # Does not need to down-/upgrade, move on to next package
                    continue
            except Exception:
                # Must not be installed, continue with installation
                pass
            # Check if package is installable
            if not pkg.check():
                if force or ("later version" in pkg._failure_string and allow_downgrade):
                    pass
                else:
                    m.fail_json(msg=pkg._failure_string)

            # add any missing deps to the list of deps we need
            # to install so they're all done in one shot
            deps_to_install.extend(pkg.missing_deps)

        except Exception as e:
            m.fail_json(msg="Unable to install package: %s" % to_native(e))

        # Install 'Recommends' of this deb file
        if install_recommends:
            pkg_recommends = get_field_of_deb(m, deb_file, "Recommends")
            deps_to_install.extend(install_recommended_packages(cache, pkg_recommends))

        # and add this deb to the list of packages to install
        pkgs_to_install.append(deb_file)

    # install the deps through apt
    retvals = {}
    if deps_to_install:
        install_dpkg_options = f"{expand_dpkg_options(dpkg_options)} -o DPkg::Lock::Timeout={lock_timeout}"
        (success, retvals) = install(m=m, pkgspec=deps_to_install, cache=cache,
                                     install_recommends=install_recommends,
                                     fail_on_autoremove=fail_on_autoremove,
                                     allow_unauthenticated=allow_unauthenticated,
                                     allow_downgrade=allow_downgrade,
                                     allow_change_held_packages=allow_change_held_packages,
                                     dpkg_options=install_dpkg_options)
        if not success:
            m.fail_json(**retvals)
        # Mark the dependencies as auto installed
        # https://github.com/ansible/ansible/issues/78123
        mark_installed(m, deps_to_install, manual=False)
        changed = retvals.get('changed', False)

    if pkgs_to_install:
        options = ' '.join(["--%s" % x for x in dpkg_options.split(",")])
        if m.check_mode:
            options += " --simulate"
        if force:
            options += " --force-all"

        cmd = "dpkg %s -i %s" % (options, " ".join(pkgs_to_install))

        with PolicyRcD(m):
            rc, out, err = m.run_command(cmd)

        if "stdout" in retvals:
            stdout = retvals["stdout"] + out
        else:
            stdout = out
        if "diff" in retvals:
            diff = retvals["diff"]
            if 'prepared' in diff:
                diff['prepared'] += '\n\n' + out
        else:
            diff = parse_diff(out)
        if "stderr" in retvals:
            stderr = retvals["stderr"] + err
        else:
            stderr = err

        if rc == 0:
            m.exit_json(changed=True, stdout=stdout, stderr=stderr, diff=diff)
        else:
            m.fail_json(msg="%s failed" % cmd, stdout=stdout, stderr=stderr)
    else:
        m.exit_json(changed=changed, stdout=retvals.get('stdout', ''), stderr=retvals.get('stderr', ''), diff=retvals.get('diff', ''))