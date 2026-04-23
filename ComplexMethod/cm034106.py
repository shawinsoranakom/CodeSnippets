def _ensure_impl(base, module_base, params):
    """Core implementation of ensure logic."""
    response = {'msg': '', 'changed': False, 'results': [], 'rc': 0}

    failures = []

    names = params.get('names', [])
    state = params.get('state')
    autoremove = params.get('autoremove', False)
    update_only = params.get('update_only', False)
    allow_downgrade = params.get('allow_downgrade', False)
    download_only = params.get('download_only', False)
    disable_gpg_check = params.get('disable_gpg_check', False)
    check_mode = params.get('check_mode', False)
    download_dir = params.get('download_dir')
    allowerasing = params.get('allowerasing', False)
    with_modules = dnf.base.WITH_MODULES and module_base is not None

    if not names and autoremove:
        names = []
        state = 'absent'

    if names == ['*'] and state == 'latest':
        try:
            base.upgrade_all()
        except dnf.exceptions.DepsolveError as e:
            raise _DnfScriptError(msg=f'Depsolve Error occurred attempting to upgrade all packages: {e}', rc=1)
    else:
        pkg_specs, group_specs, module_specs, filenames = _parse_spec_group_file(base, module_base, names, update_only, with_modules)

        pkg_specs = [p.strip() for p in pkg_specs]
        filenames = [f.strip() for f in filenames]
        groups = []
        environments = []

        for group_spec in (g.strip() for g in group_specs):
            group = base.comps.group_by_pattern(group_spec)
            if group:
                groups.append(group.id)
            else:
                environment = base.comps.environment_by_pattern(group_spec)
                if environment:
                    environments.append(environment.id)
                else:
                    raise _DnfScriptError(f'No group {group_spec} available.')

        if state in ['installed', 'present']:
            if filenames:
                _install_remote_rpms_helper(base, filenames, update_only, allow_downgrade)
                for filename in filenames:
                    response['results'].append(f'Installed {filename}')

            if module_specs and with_modules:
                for module in module_specs:
                    if not _is_module_installed(base, module_base, module, with_modules):
                        response['results'].append(f'Module {module} installed.')
                    try:
                        module_base.install([module])
                        module_base.enable([module])
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')

            for group in groups:
                try:
                    count = base.group_install(group, dnf.const.GROUP_PACKAGE_TYPES)
                    if count == 0:
                        response['results'].append(f'Group {group} already installed.')
                    else:
                        response['results'].append(f'Group {group} installed.')
                except dnf.exceptions.DepsolveError:
                    raise _DnfScriptError(msg=f'Depsolve Error occurred attempting to install group: {group}', failures=failures, results=response['results'])
                except dnf.exceptions.Error as e:
                    failures.append(f'{group} {e}')

            for environment in environments:
                try:
                    base.environment_install(environment, dnf.const.GROUP_PACKAGE_TYPES)
                except dnf.exceptions.DepsolveError:
                    raise _DnfScriptError(
                        msg=f'Depsolve Error occurred attempting to install environment: {environment}', failures=failures, results=response['results']
                    )
                except dnf.exceptions.Error as e:
                    failures.append(f'{environment} {e}')

            if module_specs and not with_modules:
                raise _DnfScriptError(f'No group {module_specs[0]} available.')

            if update_only:
                not_installed = _update_only_helper(base, pkg_specs)
                for spec in not_installed:
                    response['results'].append(f'Packages providing {spec} not installed due to update_only specified')
            else:
                for pkg_spec in pkg_specs:
                    install_result = _mark_package_install(base, pkg_spec, False, allow_downgrade)
                    if install_result['failed']:
                        failures.append(_sanitize_install_error(pkg_spec, install_result['failure']))
                    else:
                        if install_result['msg']:
                            response['results'].append(install_result['msg'])

        elif state == 'latest':
            if filenames:
                _install_remote_rpms_helper(base, filenames, update_only, allow_downgrade)
                for filename in filenames:
                    response['results'].append(f'Installed {filename}')

            if module_specs and with_modules:
                for module in module_specs:
                    try:
                        if _is_module_installed(base, module_base, module, with_modules):
                            module_base.upgrade([module])
                            response['results'].append(f'Module {module} upgraded.')
                        else:
                            module_base.install([module])
                            module_base.enable([module])
                            response['results'].append("Module {0} installed.".format(module))
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')

            for group in groups:
                try:
                    base.group_upgrade(group)
                    response['results'].append(f'Group {group} upgraded.')
                except dnf.exceptions.CompsError:
                    if not update_only:
                        try:
                            count = base.group_install(group, dnf.const.GROUP_PACKAGE_TYPES)
                            if count == 0:
                                response['results'].append(f'Group {group} already installed.')
                            else:
                                response['results'].append(f'Group {group} installed.')
                        except dnf.exceptions.Error as e2:
                            failures.append(f'{group} {e2}')
                except dnf.exceptions.Error as e:
                    failures.append(f'{group} {e}')

            for environment in environments:
                try:
                    base.environment_upgrade(environment)
                except dnf.exceptions.CompsError:
                    try:
                        base.environment_install(environment, dnf.const.GROUP_PACKAGE_TYPES)
                    except dnf.exceptions.DepsolveError as e2:
                        failures.append(f'{environment} {e2}')
                    except dnf.exceptions.Error as e2:
                        failures.append(f'{environment} {e2}')
                except dnf.exceptions.DepsolveError as e:
                    failures.append(f'{environment} {e}')
                except dnf.exceptions.Error as e:
                    failures.append(f'{environment} {e}')

            if update_only:
                not_installed = _update_only_helper(base, pkg_specs)
                for spec in not_installed:
                    response['results'].append(f'Packages providing {spec} not installed due to update_only specified')
            else:
                for pkg_spec in pkg_specs:
                    install_result = _mark_package_install(base, pkg_spec, True, allow_downgrade)
                    if install_result['failed']:
                        failures.append(_sanitize_install_error(pkg_spec, install_result['failure']))
                    else:
                        if install_result['msg']:
                            response['results'].append(install_result['msg'])

        else:
            if filenames:
                raise _DnfScriptError('Cannot remove paths -- please specify package name.')

            if module_specs and with_modules:
                for module in module_specs:
                    if _is_module_installed(base, module_base, module, with_modules):
                        response['results'].append(f'Module {module} removed.')
                    try:
                        module_base.remove([module])
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')
                    try:
                        module_base.disable([module])
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')
                    try:
                        module_base.reset([module])
                    except dnf.exceptions.MarkingErrors as e:
                        failures.append(f'{module} {e}')

            for group in groups:
                try:
                    base.group_remove(group)
                except dnf.exceptions.CompsError as e:
                    response['results'].append(f'{group} {e}')

            for environment in environments:
                try:
                    base.environment_remove(environment)
                except dnf.exceptions.CompsError as e:
                    response['results'].append(f'{environment} {e}')

            for pkg_spec in pkg_specs:
                try:
                    base.remove(pkg_spec)
                except dnf.exceptions.MarkingError as e:
                    response['results'].append(f'{e.value}: {pkg_spec}')

            allowerasing = True

            if autoremove:
                base.autoremove()

    try:
        has_changes = base.resolve(allow_erasing=allowerasing)
    except dnf.exceptions.DepsolveError as e:
        raise _DnfScriptError(msg=f'Depsolve Error occurred: {e}', failures=failures, results=response['results'])
    except dnf.exceptions.Error as e:
        raise _DnfScriptError(msg=f'Unknown Error occurred: {e}', failures=failures, results=response['results'])

    if not has_changes:
        if failures:
            raise _DnfScriptError(msg='Failed to install some of the specified packages', failures=failures, results=response['results'])
        response['msg'] = 'Nothing to do'
        return response
    else:
        response['changed'] = True

        install_action = 'Downloaded' if download_only else 'Installed'
        for package in base.transaction.install_set:
            response['results'].append(f'{install_action}: {package}')
        for package in base.transaction.remove_set:
            response['results'].append(f'Removed: {package}')

        if failures:
            raise _DnfScriptError(msg='Failed to install some of the specified packages', failures=failures, results=response['results'])

        if check_mode:
            response['msg'] = 'Check mode: No changes made, but would have if not in check mode'
            return response

        if download_only and download_dir and base.conf.destdir:
            dnf.util.ensure_dir(base.conf.destdir)
            base.repos.all().pkgdir = base.conf.destdir

        try:
            base.download_packages(base.transaction.install_set)
        except dnf.exceptions.DownloadError as e:
            raise _DnfScriptError(msg=f'Failed to download packages: {e}', failures=failures, results=response['results'])

        if not disable_gpg_check:
            for package in base.transaction.install_set:
                gpgres, gpgerr = base._sig_check_pkg(package)
                if gpgres != 0:  # Not validated successfully
                    if gpgres == 1:  # Need to install cert
                        try:
                            base._get_key_for_package(package)
                        except dnf.exceptions.Error as e:
                            raise _DnfScriptError(f'Failed to validate GPG signature for {package}: {e}')
                    else:  # Fatal error
                        raise _DnfScriptError(f'Failed to validate GPG signature for {package}: {gpgerr}')

        if download_only:
            return response
        else:
            tid = base.do_transaction()
            if tid is not None:
                transaction = base.history.old([tid])[0]
                if transaction.return_code:
                    failures.extend(transaction.output())

        if failures:
            raise _DnfScriptError(msg='Failed to install some of the specified packages', failures=failures, results=response['results'])

        return response