def version_added(v, error_code='version-added-invalid', accept_historical=False):
    if 'version_added' in v:
        version_added = v.get('version_added')
        if isinstance(version_added, str):
            # If it is not a string, schema validation will have already complained
            # - or we have a float and we are in ansible/ansible, in which case we're
            # also happy.
            if v.get('version_added_collection') == 'ansible.builtin':
                if version_added == 'historical' and accept_historical:
                    return v
                try:
                    version = StrictVersion()
                    version.parse(version_added)
                except ValueError as exc:
                    raise _add_ansible_error_code(
                        Invalid('version_added (%r) is not a valid ansible-core version: '
                                '%s' % (version_added, exc)),
                        error_code=error_code)
            else:
                try:
                    version = SemanticVersion()
                    version.parse(version_added)
                    if version.major != 0 and version.patch != 0:
                        raise _add_ansible_error_code(
                            Invalid('version_added (%r) must be a major or minor release, '
                                    'not a patch release (see specification at '
                                    'https://semver.org/)' % (version_added, )),
                            error_code='version-added-must-be-major-or-minor')
                except ValueError as exc:
                    raise _add_ansible_error_code(
                        Invalid('version_added (%r) is not a valid collection version '
                                '(see specification at https://semver.org/): '
                                '%s' % (version_added, exc)),
                        error_code=error_code)
    elif 'version_added_collection' in v:
        # Must have been manual intervention, since version_added_collection is only
        # added automatically when version_added is present
        raise Invalid('version_added_collection cannot be specified without version_added')
    return v