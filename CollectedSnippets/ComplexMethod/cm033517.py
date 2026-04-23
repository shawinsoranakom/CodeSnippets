def test_ensure_all_plugins_tested() -> None:
    """Ensure all plugins have at least one entry in the test data set, accounting for functions which have multiple names."""
    test_plugins: list[AnsibleJinja2Test] = [plugin for plugin in test_loader.all() if plugin.ansible_name.startswith('ansible.builtin.')]
    plugin_aliases: dict[t.Any, set[str]] = collections.defaultdict(set)

    for test_plugin in test_plugins:
        plugin_aliases[test_plugin.j2_function].add(test_plugin.ansible_name)

    missing_entries: list[str] = []

    for plugin_names in plugin_aliases.values():
        matching_tests = {_expected for _value, test, _expected, _extra in TEST_DATA_SET if f'ansible.builtin.{test}' in plugin_names}
        missing = {True, False} - matching_tests

        if missing:  # pragma: nocover
            missing_entries.append(f'{plugin_names}: {missing}')

    assert not missing_entries