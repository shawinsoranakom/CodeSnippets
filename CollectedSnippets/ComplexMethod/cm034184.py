def _get_galaxy_server_configs(self):

        output = []
        # add galaxy servers
        for server in self._galaxy_servers:
            server_config = {}
            s_config = self.config.get_configuration_definitions('galaxy_server', server)
            for setting in s_config.keys():
                try:
                    v, o = C.config.get_config_value_and_origin(setting, plugin_type='galaxy_server', plugin_name=server, cfile=self.config_file)
                except AnsibleError as e:
                    if s_config[setting].get('required', False):
                        v = None
                        o = 'REQUIRED'
                    else:
                        raise e
                if v is None and o is None:
                    # not all cases will be error
                    o = 'REQUIRED'
                server_config[setting] = {
                    'name': setting,
                    'value': v,
                    'origin': o,
                    'type': None
                }
            if context.CLIARGS['format'] == 'display':
                if not context.CLIARGS['only_changed'] or server_config:
                    equals = '=' * len(server)
                    output.append(f'\n{server}\n{equals}')
                    output.extend(self._render_settings(server_config))
            else:
                output.append({server: server_config})

        return output