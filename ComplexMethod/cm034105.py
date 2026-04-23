def _mark_package_install(base, pkg_spec, upgrade, allow_downgrade):
    """Mark a package for installation."""
    msg = ''
    strict = base.conf.strict

    try:
        if dnf.util.is_glob_pattern(pkg_spec):
            if upgrade:
                try:
                    base.upgrade(pkg_spec)
                except dnf.exceptions.PackagesNotInstalledError:
                    pass

            try:
                base.install(pkg_spec, strict=strict)
            except dnf.exceptions.MarkingError as e:
                msg = f'No package {pkg_spec} available.'
                if strict:
                    return {'failed': True, 'msg': msg, 'failure': f'{pkg_spec} {e}', 'rc': 1}
            except dnf.exceptions.DepsolveError as e:
                return {'failed': True, 'msg': f'Depsolve Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}
            except dnf.exceptions.Error as e:
                return {'failed': True, 'msg': f'Unknown Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}
        elif _is_newer_version_installed(base, pkg_spec):
            if allow_downgrade:
                try:
                    base.install(pkg_spec, strict=strict)
                except dnf.exceptions.MarkingError as e:
                    msg = f'No package {pkg_spec} available.'
                    if strict:
                        return {'failed': True, 'msg': msg, 'failure': f'{pkg_spec} {e}', 'rc': 1}
        elif _is_package_installed(base, pkg_spec):
            if upgrade:
                try:
                    base.upgrade(pkg_spec)
                except dnf.exceptions.PackagesNotInstalledError:
                    pass
        else:
            try:
                base.install(pkg_spec, strict=strict)
            except dnf.exceptions.MarkingError as e:
                msg = f'No package {pkg_spec} available.'
                if strict:
                    return {'failed': True, 'msg': msg, 'failure': f'{pkg_spec} {e}', 'rc': 1}
            except dnf.exceptions.DepsolveError as e:
                return {'failed': True, 'msg': f'Depsolve Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}
            except dnf.exceptions.Error as e:
                return {'failed': True, 'msg': f'Unknown Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}
    except Exception as e:
        return {'failed': True, 'msg': f'Unknown Error occurred for package {pkg_spec}.', 'failure': f'{pkg_spec} {e}', 'rc': 1}

    return {'failed': False, 'msg': msg, 'failure': '', 'rc': 0}