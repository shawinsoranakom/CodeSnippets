def main():

    # get supported pkg managers
    PKG_MANAGERS = get_all_pkg_managers()
    PKG_MANAGER_NAMES = sorted([x.lower() for x in PKG_MANAGERS.keys()])
    # add aliases
    PKG_MANAGER_NAMES.extend([alias for alist in ALIASES.values() for alias in alist])

    # start work
    global module

    # choices are not set for 'manager' as they are computed dynamically and validated below instead of in argspec
    module = AnsibleModule(argument_spec=dict(manager={'type': 'list', 'elements': 'str', 'default': ['auto']},
                                              strategy={'choices': ['first', 'all'], 'default': 'first'}),
                           supports_check_mode=True)
    packages = {}
    results = {'ansible_facts': {}}
    managers = [x.lower() for x in module.params['manager']]
    strategy = module.params['strategy']

    if 'auto' in managers:
        # keep order from user, we do dedupe below
        managers.extend(PKG_MANAGER_NAMES)
        managers.remove('auto')

    unsupported = set(managers).difference(PKG_MANAGER_NAMES)
    if unsupported:
        if 'auto' in module.params['manager']:
            msg = 'Could not auto detect a usable package manager, check warnings for details.'
        else:
            msg = 'Unsupported package managers requested: %s' % (', '.join(unsupported))
        module.fail_json(msg=msg)

    found = 0
    seen = set()
    for pkgmgr in managers:

        if strategy == 'first' and found:
            break

        # substitute aliases for aliased
        for aliased in ALIASES.keys():
            if pkgmgr in ALIASES[aliased]:
                pkgmgr = aliased
                break

        # dedupe as per above
        if pkgmgr in seen:
            continue

        seen.add(pkgmgr)

        manager = PKG_MANAGERS[pkgmgr]()
        try:
            packages_found = {}
            if manager.is_available(handle_exceptions=False):
                try:
                    packages_found = manager.get_packages()
                except Exception as e:
                    module.warn('Failed to retrieve packages with %s: %s' % (pkgmgr, to_text(e)))

            # only consider 'found' if it results in something
            if packages_found:
                found += 1
                for k in packages_found.keys():
                    if k in packages:
                        packages[k].extend(packages_found[k])
                    else:
                        packages[k] = packages_found[k]
            else:
                module.warn('Found "%s" but no associated packages' % (pkgmgr))

        except Exception as e:
            if pkgmgr in module.params['manager']:
                module.warn('Requested package manager %s was not usable by this module: %s' % (pkgmgr, to_text(e)))

    if found == 0:
        msg = ('Could not detect a supported package manager from the following list: %s, '
               'or the required Python library is not installed. Check warnings for details.' % managers)
        module.fail_json(msg=msg)

    # Set the facts, this will override the facts in ansible_facts that might exist from previous runs
    # when using operating system level or distribution package managers
    results['ansible_facts']['packages'] = packages

    module.exit_json(**results)