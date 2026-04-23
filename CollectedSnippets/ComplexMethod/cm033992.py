def _resolve_option_variables(self, variables, templar):
        """
        Return a dict of variable -> templated value, for any variables that
        that match options registered by this plugin.
        """
        # create dict of 'templated vars'
        var_options = {
            '_extras': {},
        }
        for var_name in C.config.get_plugin_vars('connection', self._load_name):
            if var_name in variables:
                try:
                    var_options[var_name] = templar.template(variables[var_name])
                except AnsibleValueOmittedError:
                    pass

        # add extras if plugin supports them
        if getattr(self, 'allow_extras', False):
            for var_name in variables:
                if var_name.startswith(f'ansible_{self.extras_prefix}_') and var_name not in var_options:
                    try:
                        var_options['_extras'][var_name] = templar.template(variables[var_name])
                    except AnsibleValueOmittedError:
                        pass

        return var_options