def execute_validate(self):

        found = False
        config_entries = self._list_entries_from_args()
        plugin_types = config_entries.pop('PLUGINS', None)
        galaxy_servers = config_entries.pop('GALAXY_SERVERS', None)

        if context.CLIARGS['format'] == 'ini':
            if C.CONFIG_FILE is not None:
                # validate ini config since it is found

                sections = _get_ini_entries(config_entries)
                # Also from plugins
                if plugin_types:
                    for ptype in plugin_types:
                        for plugin in plugin_types[ptype].keys():
                            plugin_sections = _get_ini_entries(plugin_types[ptype][plugin])
                            for s in plugin_sections:
                                if s in sections:
                                    sections[s].update(plugin_sections[s])
                                else:
                                    sections[s] = plugin_sections[s]
                if galaxy_servers:
                    for server in galaxy_servers:
                        server_sections = _get_ini_entries(galaxy_servers[server])
                        for s in server_sections:
                            if s in sections:
                                sections[s].update(server_sections[s])
                            else:
                                sections[s] = server_sections[s]
                if sections:
                    p = C.config._parsers[C.CONFIG_FILE]
                    for s in p.sections():
                        # check for valid sections
                        if s not in sections:
                            display.error(f"Found unknown section '{s}' in '{C.CONFIG_FILE}.")
                            found = True
                            continue

                        # check keys in valid sections
                        for k in p.options(s):
                            if k not in sections[s]:
                                display.error(f"Found unknown key '{k}' in section '{s}' in '{C.CONFIG_FILE}.")
                                found = True

        elif context.CLIARGS['format'] == 'env':
            # validate any 'ANSIBLE_' env vars found
            evars = [varname for varname in os.environ.keys() if _ansible_env_vars(varname)]
            if evars:
                data = _get_evar_list(config_entries)
                if plugin_types:
                    for ptype in plugin_types:
                        for plugin in plugin_types[ptype].keys():
                            data.extend(_get_evar_list(plugin_types[ptype][plugin]))

                for evar in evars:
                    if evar not in data:
                        display.error(f"Found unknown environment variable '{evar}'.")
                        found = True

        # we found discrepancies!
        if found:
            sys.exit(1)

        # allsgood
        display.display("All configurations seem valid!")