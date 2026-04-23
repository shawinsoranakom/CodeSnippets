def parse(self, inventory: InventoryData, loader: DataLoader, path: str, cache: bool = False) -> None:
        super(InventoryModule, self).parse(inventory, loader, path)

        self.set_options()

        origin = Origin(description=f'<inventory script output from {path!r}>')

        data, stderr, stderr_help_text = run_command(path, ['--list'], origin)

        try:
            profile_name = detect_profile_name(data)
            decoder = get_decoder(profile_name)
        except Exception as ex:
            raise AnsibleError(
                message="Unable to get JSON decoder for inventory script result.",
                help_text=stderr_help_text,
                # obj will be added by inventory manager
            ) from ex

        try:
            try:
                processed = json.loads(data, cls=decoder)
            except Exception as json_ex:
                AnsibleJSONParserError.handle_exception(json_ex, origin)
        except Exception as ex:
            raise AnsibleError(
                message="Inventory script result could not be parsed as JSON.",
                help_text=stderr_help_text,
                # obj will be added by inventory manager
            ) from ex

        # if no other errors happened, and you want to force displaying stderr, do so now
        if stderr and self.get_option('always_show_stderr'):
            self.display.error(msg=stderr)

        data_from_meta: dict | None = None

        # A "_meta" subelement may contain a variable "hostvars" which contains a hash for each host
        # if this "hostvars" exists at all then do not call --host for each # host.
        # This is for efficiency and scripts should still return data
        # if called with --host for backwards compat with 1.2 and earlier.
        for (group, gdata) in processed.items():
            if group == '_meta':
                data_from_meta = gdata.get('hostvars')

                if not isinstance(data_from_meta, dict):
                    raise TypeError(f"Value contains '_meta.hostvars' which is {native_type_name(data_from_meta)!r} instead of {native_type_name(dict)!r}.")
            else:
                self._parse_group(group, gdata, origin)

        if data_from_meta is None:
            display.deprecated(
                msg="Inventory scripts should always provide 'meta.hostvars'. "
                    "Host variables will be collected by running the inventory script with the '--host' option for each host.",
                version='2.23',
                obj=origin,
            )

        for host in self._hosts:
            if data_from_meta is None:
                got = self.get_host_variables(path, host, origin)
            else:
                got = data_from_meta.get(host, {})

            self._populate_host_vars([host], got)