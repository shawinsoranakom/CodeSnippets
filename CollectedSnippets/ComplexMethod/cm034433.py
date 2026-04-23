def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'build-dep', 'fixed', 'latest', 'present']),
            update_cache=dict(type='bool', aliases=['update-cache']),
            update_cache_retries=dict(type='int', default=5),
            update_cache_retry_max_delay=dict(type='int', default=12),
            cache_valid_time=dict(type='int', default=0),
            purge=dict(type='bool', default=False),
            package=dict(type='list', elements='str', aliases=['pkg', 'name']),
            deb=dict(type='path'),
            default_release=dict(type='str', aliases=['default-release']),
            install_recommends=dict(type='bool', aliases=['install-recommends']),
            force=dict(type='bool', default=False),
            upgrade=dict(type='str', choices=['dist', 'full', 'no', 'safe', 'yes'], default='no'),
            dpkg_options=dict(type='str', default=DPKG_OPTIONS),
            autoremove=dict(type='bool', default=False),
            autoclean=dict(type='bool', default=False),
            fail_on_autoremove=dict(type='bool', default=False),
            policy_rc_d=dict(type='int', default=None),
            only_upgrade=dict(type='bool', default=False),
            force_apt_get=dict(type='bool', default=False),
            clean=dict(type='bool', default=False),
            allow_unauthenticated=dict(type='bool', default=False, aliases=['allow-unauthenticated']),
            allow_downgrade=dict(type='bool', default=False, aliases=['allow-downgrade', 'allow_downgrades', 'allow-downgrades']),
            allow_change_held_packages=dict(type='bool', default=False),
            lock_timeout=dict(type='int', default=60),
            auto_install_module_deps=dict(type='bool', default=True),
        ),
        mutually_exclusive=[['deb', 'package', 'upgrade']],
        required_one_of=[['autoremove', 'deb', 'package', 'update_cache', 'upgrade']],
        supports_check_mode=True,
    )

    # We screenscrape apt-get and aptitude output for information so we need
    # to make sure we use the best parsable locale when running commands
    # also set apt specific vars for desired behaviour
    locale = get_best_parsable_locale(module)
    locale_module.setlocale(locale_module.LC_ALL, locale)
    # APT related constants
    APT_ENV_VARS = dict(
        DEBIAN_FRONTEND='noninteractive',
        DEBIAN_PRIORITY='critical',
        LANG=locale,
        LC_ALL=locale,
        LC_MESSAGES=locale,
        LC_CTYPE=locale,
        LANGUAGE=locale,
    )
    module.run_command_environ_update = APT_ENV_VARS

    global APTITUDE_CMD
    APTITUDE_CMD = module.get_bin_path("aptitude", False)
    global APT_GET_CMD
    APT_GET_CMD = module.get_bin_path("apt-get")

    p = module.params
    install_recommends = p['install_recommends']
    dpkg_options = f"{expand_dpkg_options(p['dpkg_options'])} -o DPkg::Lock::Timeout={p['lock_timeout']}"

    if not HAS_PYTHON_APT:
        # This interpreter can't see the apt Python library- we'll do the following to try and fix that:
        # 1) look in common locations for system-owned interpreters that can see it; if we find one, respawn under it
        # 2) finding none, try to install a matching python3-apt package for the current interpreter version;
        #    we limit to the current interpreter version to try and avoid installing a whole other Python just
        #    for apt support
        # 3) if we installed a support package, try to respawn under what we think is the right interpreter (could be
        #    the current interpreter again, but we'll let it respawn anyway for simplicity)
        # 4) if still not working, return an error and give up (some corner cases not covered, but this shouldn't be
        #    made any more complex than it already is to try and cover more, eg, custom interpreters taking over
        #    system locations)

        apt_pkg_name = 'python3-apt'

        if has_respawned():
            # this shouldn't be possible; short-circuit early if it happens...
            module.fail_json(msg="{0} must be installed and visible from {1}.".format(apt_pkg_name, sys.executable))

        interpreters = ['/usr/bin/python3', '/usr/bin/python']

        interpreter = probe_interpreters_for_module(interpreters, 'apt')

        if interpreter:
            # found the Python bindings; respawn this module under the interpreter where we found them
            respawn_module(interpreter)
            # this is the end of the line for this process, it will exit here once the respawned module has completed

        # don't make changes if we're in check_mode
        if module.check_mode:
            module.fail_json(
                msg=f"{apt_pkg_name} must be installed to use check mode. "
                    "If run normally this module can auto-install it, "
                    "see the auto_install_module_deps option.",
            )
        elif p['auto_install_module_deps']:
            # We skip cache update in auto install the dependency if the
            # user explicitly declared it with update_cache=no.
            if module.params.get('update_cache') is False:
                module.warn("Auto-installing missing dependency without updating cache: %s" % apt_pkg_name)
            else:
                module.warn("Updating cache and auto-installing missing dependency: %s" % apt_pkg_name)
                module.run_command([APT_GET_CMD, 'update'], check_rc=True)

            # try to install the apt Python binding
            apt_pkg_cmd = [APT_GET_CMD, 'install', apt_pkg_name, '-y', '-q', dpkg_options]

            if install_recommends is False:
                apt_pkg_cmd.extend(["-o", "APT::Install-Recommends=no"])
            elif install_recommends is True:
                apt_pkg_cmd.extend(["-o", "APT::Install-Recommends=yes"])
            # install_recommends is None uses the OS default

            module.run_command(apt_pkg_cmd, check_rc=True)

            # try again to find the bindings in common places
            interpreter = probe_interpreters_for_module(interpreters, 'apt')

            if interpreter:
                # found the Python bindings; respawn this module under the interpreter where we found them
                # NB: respawn is somewhat wasteful if it's this interpreter, but simplifies the code
                respawn_module(interpreter)
                # this is the end of the line for this process, it will exit here once the respawned module has completed

        # we've done all we can do; just tell the user it's busted and get out
        py_version = sys.version.replace("\n", "")
        module.fail_json(
            msg=f"Could not import the {apt_pkg_name} module using {sys.executable} ({py_version}). "
            f"Ensure {apt_pkg_name} package is installed (either manually or via the auto_install_module_deps option) "
            f"or that you have specified the correct ansible_python_interpreter. (attempted {interpreters}).",
        )

    if p['clean'] is True:
        aptclean_stdout, aptclean_stderr, aptclean_diff = aptclean(module)
        # If there is nothing else to do exit. This will set state as
        #  changed based on if the cache was updated.
        if not p['package'] and p['upgrade'] == 'no' and not p['deb']:
            module.exit_json(
                changed=True,
                msg=aptclean_stdout,
                stdout=aptclean_stdout,
                stderr=aptclean_stderr,
                diff=aptclean_diff
            )

    if p['upgrade'] == 'no':
        p['upgrade'] = None

    use_apt_get = p['force_apt_get']

    if not use_apt_get and not APTITUDE_CMD:
        use_apt_get = True

    updated_cache = False
    updated_cache_time = 0
    allow_unauthenticated = p['allow_unauthenticated']
    allow_downgrade = p['allow_downgrade']
    allow_change_held_packages = p['allow_change_held_packages']
    autoremove = p['autoremove']
    fail_on_autoremove = p['fail_on_autoremove']
    autoclean = p['autoclean']

    # max times we'll retry
    deadline = time.time() + p['lock_timeout']

    # keep running on lock issues unless timeout or resolution is hit.
    while True:

        # Get the cache object, this has 3 retries built in
        cache = get_cache(module)

        try:
            if p['default_release']:
                try:
                    apt_pkg.config['APT::Default-Release'] = p['default_release']
                except AttributeError:
                    apt_pkg.Config['APT::Default-Release'] = p['default_release']
                # reopen cache w/ modified config
                cache.open(progress=None)

            mtimestamp, updated_cache_time = get_updated_cache_time()
            # Cache valid time is default 0, which will update the cache if
            #  needed and `update_cache` was set to true
            updated_cache = False
            if p['update_cache'] or p['cache_valid_time']:
                now = datetime.datetime.now()
                tdelta = datetime.timedelta(seconds=p['cache_valid_time'])
                if not mtimestamp + tdelta >= now:
                    # Retry to update the cache with exponential backoff
                    err = ''
                    update_cache_retries = module.params.get('update_cache_retries')
                    update_cache_retry_max_delay = module.params.get('update_cache_retry_max_delay')
                    randomize = secrets.randbelow(1000) / 1000.0

                    for retry in range(update_cache_retries):
                        try:
                            if not module.check_mode:
                                cache.update()
                            break
                        except apt.cache.FetchFailedException as fetch_failed_exc:
                            err = fetch_failed_exc
                            module.warn(
                                f"Failed to update cache after {retry + 1} retries due "
                                f"to {to_native(fetch_failed_exc)}, retrying"
                            )

                        # Use exponential backoff plus a little bit of randomness
                        delay = 2 ** retry + randomize
                        if delay > update_cache_retry_max_delay:
                            delay = update_cache_retry_max_delay + randomize
                        time.sleep(delay)
                        module.warn(f"Sleeping for {int(round(delay))} seconds, before attempting to refresh the cache again")
                    else:
                        msg = (
                            f"Failed to update apt cache after {update_cache_retries} retries: "
                            f"{err if err else 'unknown reason'}"
                        )
                        module.fail_json(msg=msg)

                    cache.open(progress=None)
                    mtimestamp, post_cache_update_time = get_updated_cache_time()
                    if module.check_mode or updated_cache_time != post_cache_update_time:
                        updated_cache = True
                    updated_cache_time = post_cache_update_time

                # If there is nothing else to do exit. This will set state as
                #  changed based on if the cache was updated.
                if not p['package'] and not p['upgrade'] and not p['deb']:
                    module.exit_json(
                        changed=updated_cache,
                        cache_updated=updated_cache,
                        cache_update_time=updated_cache_time
                    )

            force_yes = p['force']

            if p['upgrade']:
                upgrade(
                    module,
                    p['upgrade'],
                    force_yes,
                    p['default_release'],
                    use_apt_get,
                    dpkg_options,
                    autoremove,
                    fail_on_autoremove,
                    allow_unauthenticated,
                    allow_downgrade
                )

            if p['deb']:
                if p['state'] != 'present':
                    module.fail_json(msg="deb only supports state=present")
                if '://' in p['deb']:
                    p['deb'] = fetch_file(module, p['deb'])
                install_deb(module, p['deb'], cache,
                            install_recommends=install_recommends,
                            allow_unauthenticated=allow_unauthenticated,
                            allow_change_held_packages=allow_change_held_packages,
                            allow_downgrade=allow_downgrade,
                            force=force_yes,
                            fail_on_autoremove=fail_on_autoremove,
                            dpkg_options=p['dpkg_options'],
                            lock_timeout=p['lock_timeout']
                            )

            unfiltered_packages = p['package'] or ()
            packages = [package.strip() for package in unfiltered_packages if package != '*']
            all_installed = '*' in unfiltered_packages
            latest = p['state'] == 'latest'

            if latest and all_installed:
                if packages:
                    module.fail_json(msg='unable to install additional packages when upgrading all installed packages')
                upgrade(
                    module,
                    'yes',
                    force_yes,
                    p['default_release'],
                    use_apt_get,
                    dpkg_options,
                    autoremove,
                    fail_on_autoremove,
                    allow_unauthenticated,
                    allow_downgrade
                )

            if packages:
                for package in packages:
                    if package.count('=') > 1:
                        module.fail_json(msg="invalid package spec: %s" % package)

            if not packages:
                if autoclean:
                    cleanup(module, p['purge'], force=force_yes, operation='autoclean', dpkg_options=dpkg_options)
                if autoremove:
                    cleanup(module, p['purge'], force=force_yes, operation='autoremove', dpkg_options=dpkg_options)

            if p['state'] in ('latest', 'present', 'build-dep', 'fixed'):
                state_upgrade = False
                state_builddep = False
                state_fixed = False
                if p['state'] == 'latest':
                    state_upgrade = True
                if p['state'] == 'build-dep':
                    state_builddep = True
                if p['state'] == 'fixed':
                    state_fixed = True

                success, retvals = install(
                    module,
                    packages,
                    cache,
                    upgrade=state_upgrade,
                    default_release=p['default_release'],
                    install_recommends=install_recommends,
                    force=force_yes,
                    dpkg_options=dpkg_options,
                    build_dep=state_builddep,
                    fixed=state_fixed,
                    autoremove=autoremove,
                    fail_on_autoremove=fail_on_autoremove,
                    only_upgrade=p['only_upgrade'],
                    allow_unauthenticated=allow_unauthenticated,
                    allow_downgrade=allow_downgrade,
                    allow_change_held_packages=allow_change_held_packages,
                )

                # Store if the cache has been updated
                retvals['cache_updated'] = updated_cache
                # Store when the update time was last
                retvals['cache_update_time'] = updated_cache_time

                if success:
                    module.exit_json(**retvals)
                else:
                    module.fail_json(**retvals)
            elif p['state'] == 'absent':
                remove(
                    module,
                    packages,
                    cache,
                    p['purge'],
                    force=force_yes,
                    dpkg_options=dpkg_options,
                    autoremove=autoremove,
                    allow_change_held_packages=allow_change_held_packages
                )

        except apt.cache.LockFailedException as lockFailedException:
            if time.time() < deadline:
                continue
            module.fail_json(msg="Failed to lock apt for exclusive operation: %s" % lockFailedException)
        except apt.cache.FetchFailedException as fetchFailedException:
            module.fail_json(msg="Could not fetch updated apt files: %s" % fetchFailedException)

        # got here w/o exception and/or exit???
        module.fail_json(msg='Unexpected code path taken, we really should have exited before, this is a bug')