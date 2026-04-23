def update_vars(self, variables: dict[str, t.Any]) -> None:
        """
        Adds 'magic' variables relating to connections to the variable dictionary provided.
        In case users need to access from the play, this is a legacy from runner.
        """
        for varname in C.COMMON_CONNECTION_VARS:
            value = None
            if varname in variables:
                # dont update existing
                continue
            elif 'password' in varname or 'passwd' in varname:
                # no secrets!
                continue
            elif varname == 'ansible_connection':
                # its me mom!
                value = self._load_name
            elif varname == 'ansible_shell_type' and self._shell:
                # its my cousin ...
                value = self._shell._load_name
            else:
                # deal with generic options if the plugin supports em (for example not all connections have a remote user)
                options = C.config.get_plugin_options_from_var('connection', self._load_name, varname)
                if options:
                    value = self.get_option(options[0])  # for these variables there should be only one option
                elif 'become' not in varname:
                    # fallback to play_context, unless become related  TODO: in the end, should come from task/play and not pc
                    for prop, var_list in C.MAGIC_VARIABLE_MAPPING.items():
                        if varname in var_list:
                            try:
                                value = getattr(self._play_context, prop)
                                break
                            except AttributeError:
                                # It was not defined; fine to ignore
                                continue

            if value is not None:
                display.debug('Set connection var {0} to {1}'.format(varname, value))
                variables[varname] = value