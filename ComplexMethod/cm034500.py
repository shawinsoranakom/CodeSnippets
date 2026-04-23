def main():
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            mode=dict(type='raw'),
            update_cache=dict(type='bool', default=True, aliases=['update-cache']),
            update_cache_retries=dict(type='int', default=5),
            update_cache_retry_max_delay=dict(type='int', default=12),
            filename=dict(type='str'),
            # This should not be needed, but exists as a failsafe
            install_python_apt=dict(type='bool', default=True),
            validate_certs=dict(type='bool', default=True),
            codename=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    params = module.params
    repo = module.params['repo']
    state = module.params['state']
    update_cache = module.params['update_cache']
    # Note: mode is referenced in SourcesList class via the passed in module (self here)

    sourceslist = None

    if not HAVE_PYTHON_APT:
        # This interpreter can't see the apt Python library- we'll do the following to try and fix that:
        # 1) look in common locations for system-owned interpreters that can see it; if we find one, respawn under it
        # 2) finding none, try to install a matching python-apt package for the current interpreter version;
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
            module.fail_json(msg="%s must be installed to use check mode. "
                                 "If run normally this module can auto-install it." % apt_pkg_name)

        if params['install_python_apt']:
            install_python_apt(module, apt_pkg_name)
        else:
            module.fail_json(msg='%s is not installed, and install_python_apt is False' % apt_pkg_name)

        # try again to find the bindings in common places
        interpreter = probe_interpreters_for_module(interpreters, 'apt')

        if interpreter:
            # found the Python bindings; respawn this module under the interpreter where we found them
            # NB: respawn is somewhat wasteful if it's this interpreter, but simplifies the code
            respawn_module(interpreter)
            # this is the end of the line for this process, it will exit here once the respawned module has completed
        else:
            # we've done all we can do; just tell the user it's busted and get out
            module.fail_json(msg="{0} must be installed and visible from {1}.".format(apt_pkg_name, sys.executable))

    if not repo:
        module.fail_json(msg='Please set argument \'repo\' to a non-empty value')

    if isinstance(distro, aptsources_distro.Distribution):
        sourceslist = UbuntuSourcesList(module)
    else:
        module.fail_json(msg='Module apt_repository is not supported on target.')

    sourceslist_before = copy.deepcopy(sourceslist)
    sources_before = sourceslist.dump()

    try:
        if state == 'present':
            sourceslist.add_source(repo)
        elif state == 'absent':
            sourceslist.remove_source(repo)
    except InvalidSource as ex:
        module.fail_json(msg='Invalid repository string: %s' % to_native(ex))

    sources_after = sourceslist.dump()
    changed = sources_before != sources_after

    diff = []
    sources_added = set()
    sources_removed = set()
    if changed:
        sources_added = set(sources_after.keys()).difference(sources_before.keys())
        sources_removed = set(sources_before.keys()).difference(sources_after.keys())
        if module._diff:
            for filename in set(sources_added.union(sources_removed)):
                diff.append({'before': sources_before.get(filename, ''),
                             'after': sources_after.get(filename, ''),
                             'before_header': (filename, '/dev/null')[filename not in sources_before],
                             'after_header': (filename, '/dev/null')[filename not in sources_after]})

    if changed and not module.check_mode:
        try:
            err = ''
            sourceslist.save()
            if update_cache:
                update_cache_retries = module.params.get('update_cache_retries')
                update_cache_retry_max_delay = module.params.get('update_cache_retry_max_delay')
                randomize = secrets.randbelow(1000) / 1000.0

                cache = apt.Cache()
                for retry in range(update_cache_retries):
                    try:
                        cache.update()
                        break
                    except apt.cache.FetchFailedException as fetch_failed_exc:
                        err = fetch_failed_exc
                        module.warn(
                            f"Failed to update cache after {retry + 1} due "
                            f"to {to_native(fetch_failed_exc)} retry, retrying"
                        )

                    # Use exponential backoff with a max fail count, plus a little bit of randomness
                    delay = 2 ** retry + randomize
                    if delay > update_cache_retry_max_delay:
                        delay = update_cache_retry_max_delay + randomize
                    time.sleep(delay)
                    module.warn(f"Sleeping for {int(round(delay))} seconds, before attempting to update the cache again")
                else:
                    revert_sources_list(sources_before, sources_after, sourceslist_before)
                    msg = (
                        f"Failed to update apt cache after {update_cache_retries} retries: "
                        f"{err if err else 'unknown reason'}"
                    )
                    module.fail_json(msg=msg)

        except OSError as ex:
            revert_sources_list(sources_before, sources_after, sourceslist_before)
            raise

    module.exit_json(changed=changed, repo=repo, sources_added=sources_added, sources_removed=sources_removed, state=state, diff=diff)