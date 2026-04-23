def _parse_group(self, group: str, data: t.Any, origin: Origin) -> None:
        """Normalize and ingest host/var information for the named group."""
        group = self.inventory.add_group(group)

        if not isinstance(data, dict):
            original_type = native_type_name(data)
            data = {'hosts': data}
            display.deprecated(
                msg=f"Group {group!r} was converted to {native_type_name(dict)!r} from {original_type!r}.",
                version='2.23',
                obj=origin,
            )
        elif not any(k in data for k in ('hosts', 'vars', 'children')):
            data = {'hosts': [group], 'vars': data}
            display.deprecated(
                msg=f"Treating malformed group {group!r} as the sole host of that group. Variables provided in this manner cannot be templated.",
                version='2.23',
                obj=origin,
            )

        if (data_hosts := data.get('hosts', ...)) is not ...:
            if not isinstance(data_hosts, list):
                raise TypeError(f"Value contains '{group}.hosts' which is {native_type_name(data_hosts)!r} instead of {native_type_name(list)!r}.")

            for hostname in data_hosts:
                self._hosts.add(hostname)
                self.inventory.add_host(hostname, group)

        if (data_vars := data.get('vars', ...)) is not ...:
            if not isinstance(data_vars, dict):
                raise TypeError(f"Value contains '{group}.vars' which is {native_type_name(data_vars)!r} instead of {native_type_name(dict)!r}.")

            for k, v in data_vars.items():
                self.inventory.set_variable(group, k, v)

        if group != '_meta' and isinstance(data, dict) and 'children' in data:
            for child_name in data['children']:
                child_name = self.inventory.add_group(child_name)
                self.inventory.add_child(group, child_name)