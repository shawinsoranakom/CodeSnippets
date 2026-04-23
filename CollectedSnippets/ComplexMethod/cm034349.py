def _normalize_galaxy_yml_manifest(
        galaxy_yml,  # type: dict[str, t.Union[str, list[str], dict[str, str], None, t.Type[Sentinel]]]
        b_galaxy_yml_path,  # type: bytes
        require_build_metadata=True,  # type: bool
):
    # type: (...) -> dict[str, t.Union[str, list[str], dict[str, str], None, t.Type[Sentinel]]]
    galaxy_yml_schema = (
        get_collections_galaxy_meta_info()
    )  # type: list[dict[str, t.Any]]  # FIXME: <--
    # FIXME: 👆maybe precise type: list[dict[str, t.Union[bool, str, list[str]]]]

    mandatory_keys = set()
    string_keys = set()  # type: set[str]
    list_keys = set()  # type: set[str]
    dict_keys = set()  # type: set[str]
    sentinel_keys = set()  # type: set[str]

    for info in galaxy_yml_schema:
        if info.get('required', False):
            mandatory_keys.add(info['key'])

        key_list_type = {
            'str': string_keys,
            'list': list_keys,
            'dict': dict_keys,
            'sentinel': sentinel_keys,
        }[info.get('type', 'str')]
        key_list_type.add(info['key'])

    all_keys = frozenset(mandatory_keys | string_keys | list_keys | dict_keys | sentinel_keys)

    set_keys = set(galaxy_yml.keys())
    missing_keys = mandatory_keys.difference(set_keys)
    if missing_keys:
        msg = (
            "The collection galaxy.yml at '%s' is missing the following mandatory keys: %s"
            % (to_native(b_galaxy_yml_path), ", ".join(sorted(missing_keys)))
        )
        if require_build_metadata:
            raise AnsibleError(msg)
        display.warning(msg)
        raise ValueError(msg)

    extra_keys = set_keys.difference(all_keys)
    if len(extra_keys) > 0:
        display.warning("Found unknown keys in collection galaxy.yml at '%s': %s"
                        % (to_text(b_galaxy_yml_path), ", ".join(extra_keys)))

    # Add the defaults if they have not been set
    for optional_string in string_keys:
        if optional_string not in galaxy_yml:
            galaxy_yml[optional_string] = None

    for optional_list in list_keys:
        list_val = galaxy_yml.get(optional_list, None)

        if list_val is None:
            galaxy_yml[optional_list] = []
        elif not isinstance(list_val, list):
            galaxy_yml[optional_list] = [list_val]  # type: ignore[list-item]

    for optional_dict in dict_keys:
        if optional_dict not in galaxy_yml:
            galaxy_yml[optional_dict] = {}

    for optional_sentinel in sentinel_keys:
        if optional_sentinel not in galaxy_yml:
            galaxy_yml[optional_sentinel] = Sentinel

    # NOTE: `version: null` is only allowed for `galaxy.yml`
    # NOTE: and not `MANIFEST.json`. The use-case for it is collections
    # NOTE: that generate the version from Git before building a
    # NOTE: distributable tarball artifact.
    if not galaxy_yml.get('version'):
        galaxy_yml['version'] = '*'

    return galaxy_yml