def _parse_group(self, group, group_data):
        if group_data is not None and not isinstance(group_data, MutableMapping):
            self.display.warning("Skipping '%s' as this is not a valid group definition" % group)
            return

        group = self.inventory.add_group(group)
        if group_data is None:
            return

        for key, data in group_data.items():
            if key == 'vars':
                if not isinstance(data, MutableMapping):
                    raise AnsibleParserError(
                        'Invalid "vars" entry for "%s" group, requires a dict, found "%s" instead.' %
                        (group, type(data))
                    )
                for var, value in data.items():
                    self.inventory.set_variable(group, var, value)

            elif key == 'children':
                if not isinstance(data, MutableSequence):
                    raise AnsibleParserError(
                        'Invalid "children" entry for "%s" group, requires a list, found "%s" instead.' %
                        (group, type(data))
                    )
                for subgroup in data:
                    self._parse_group(subgroup, {})
                    self.inventory.add_child(group, subgroup)

            elif key == 'hosts':
                if not isinstance(data, MutableMapping):
                    raise AnsibleParserError(
                        'Invalid "hosts" entry for "%s" group, requires a dict, found "%s" instead.' %
                        (group, type(data))
                    )
                for host_pattern, value in data.items():
                    hosts, port = self._expand_hostpattern(host_pattern)
                    self._populate_host_vars(hosts, value, group, port)
            else:
                self.display.warning(
                    'Skipping unexpected key "%s" in group "%s", only "vars", "children" and "hosts" are valid' %
                    (key, group)
                )