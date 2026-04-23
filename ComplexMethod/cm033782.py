def check_removal_version(v, version_field, collection_name_field, error_code='invalid-removal-version'):
    version = v.get(version_field)
    collection_name = v.get(collection_name_field)
    if not isinstance(version, str) or not isinstance(collection_name, str):
        # If they are not strings, schema validation will have already complained.
        return v
    if collection_name == 'ansible.builtin':
        try:
            parsed_version = StrictVersion()
            parsed_version.parse(version)
        except ValueError as exc:
            raise _add_ansible_error_code(
                Invalid('%s (%r) is not a valid ansible-core version: %s' % (version_field, version, exc)),
                error_code=error_code)
        return v
    try:
        parsed_version = SemanticVersion()
        parsed_version.parse(version)
        if parsed_version.major != 0 and (parsed_version.minor != 0 or parsed_version.patch != 0):
            raise _add_ansible_error_code(
                Invalid('%s (%r) must be a major release, not a minor or patch release (see specification at '
                        'https://semver.org/)' % (version_field, version)),
                error_code='removal-version-must-be-major')
    except ValueError as exc:
        raise _add_ansible_error_code(
            Invalid('%s (%r) is not a valid collection version (see specification at https://semver.org/): '
                    '%s' % (version_field, version, exc)),
            error_code=error_code)
    return v