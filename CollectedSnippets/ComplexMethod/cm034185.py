def execute_dump(self):
        """
        Shows the current settings, merges ansible.cfg if specified
        """
        output = []
        if context.CLIARGS['type'] in ('base', 'all'):
            # deal with base
            output = self._get_global_configs()

            # add galaxy servers
            server_config_list = self._get_galaxy_server_configs()
            if context.CLIARGS['format'] == 'display':
                output.append('\nGALAXY_SERVERS:\n')
                output.extend(server_config_list)
            else:
                configs = {}
                for server_config in server_config_list:
                    server = list(server_config.keys())[0]
                    server_reduced_config = server_config.pop(server)
                    configs[server] = list(server_reduced_config.values())
                output.append({'GALAXY_SERVERS': configs})

        if context.CLIARGS['type'] == 'all':
            # add all plugins
            for ptype in C.CONFIGURABLE_PLUGINS:
                plugin_list = self._get_plugin_configs(ptype, context.CLIARGS['args'])
                if context.CLIARGS['format'] == 'display':
                    if not context.CLIARGS['only_changed'] or plugin_list:
                        output.append('\n%s:\n%s' % (ptype.upper(), '=' * len(ptype)))
                        output.extend(plugin_list)
                else:
                    if ptype in ('modules', 'doc_fragments'):
                        pname = ptype.upper()
                    else:
                        pname = '%s_PLUGINS' % ptype.upper()
                    output.append({pname: plugin_list})

        elif context.CLIARGS['type'] != 'base':
            # deal with specific plugin
            output = self._get_plugin_configs(context.CLIARGS['type'], context.CLIARGS['args'])

        if context.CLIARGS['format'] == 'display':
            text = '\n'.join(output)
        if context.CLIARGS['format'] == 'yaml':
            text = yaml_dump(output)
        elif context.CLIARGS['format'] == 'json':
            text = _json.json_dumps_formatted(output)

        self.pager(to_text(text, errors='surrogate_or_strict'))