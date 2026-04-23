def _set_connection_options(self, variables, templar):

        # keep list of variable names possibly consumed
        varnames = []

        # grab list of usable vars for this plugin
        option_vars = C.config.get_plugin_vars('connection', self._connection._load_name)
        varnames.extend(option_vars)

        task_keys = self._task.dump_attrs()

        # The task_keys 'timeout' attr is the task's timeout, not the connection timeout.
        # The connection timeout is threaded through the play_context for now.
        task_keys['timeout'] = self._play_context.timeout

        if self._play_context.password:
            # The connection password is threaded through the play_context for
            # now. This is something we ultimately want to avoid, but the first
            # step is to get connection plugins pulling the password through the
            # config system instead of directly accessing play_context.
            task_keys['password'] = self._play_context.password

        # Prevent task retries from overriding connection retries
        del task_keys['retries']

        # set options with 'templated vars' specific to this plugin and dependent ones
        var_options = self._connection._resolve_option_variables(variables, templar)
        self._connection.set_options(task_keys=task_keys, var_options=var_options)
        varnames.extend(self._set_plugin_options('shell', variables, templar, task_keys))

        if self._connection.become is not None:
            if self._play_context.become_pass:
                # FIXME: eventually remove from task and play_context, here for backwards compat
                # keep out of play objects to avoid accidental disclosure, only become plugin should have
                # The become pass is already in the play_context if given on
                # the CLI (-K). Make the plugin aware of it in this case.
                task_keys['become_pass'] = self._play_context.become_pass

            varnames.extend(self._set_plugin_options('become', variables, templar, task_keys))

            # FOR BACKWARDS COMPAT:
            for option in ('become_user', 'become_flags', 'become_exe', 'become_pass'):
                try:
                    setattr(self._play_context, option, self._connection.become.get_option(option))
                except KeyError:
                    pass  # some plugins don't support all base flags
            self._play_context.prompt = self._connection.become.prompt

        # deals with networking sub_plugins (network_cli/httpapi/netconf)
        sub = getattr(self._connection, '_sub_plugin', None)
        if sub and sub.get('type') != 'external':
            plugin_type = get_plugin_class(sub.get("obj"))
            varnames.extend(self._set_plugin_options(plugin_type, variables, templar, task_keys))
        sub_conn = getattr(self._connection, 'ssh_type_conn', None)
        if sub_conn is not None:
            varnames.extend(self._set_plugin_options("ssh_type_conn", variables, templar, task_keys))

        return varnames