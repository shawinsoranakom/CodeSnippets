def set_task_and_variable_override(self, task, variables, templar):
        """
        Sets attributes from the task if they are set, which will override
        those from the play.

        :arg task: the task object with the parameters that were set on it
        :arg variables: variables from inventory
        :arg templar: templar instance if templating variables is needed
        """

        new_info = self.copy()

        # loop through a subset of attributes on the task object and set
        # connection fields based on their values
        for attr in TASK_ATTRIBUTE_OVERRIDES:
            if (attr_val := getattr(task, attr, None)) is not None:
                setattr(new_info, attr, attr_val)

        # next, use the MAGIC_VARIABLE_MAPPING dictionary to update this
        # connection info object with 'magic' variables from the variable list.
        # If the value 'ansible_delegated_vars' is in the variables, it means
        # we have a delegated-to host, so we check there first before looking
        # at the variables in general
        if task.delegate_to is not None:
            # In the case of a loop, the delegated_to host may have been
            # templated based on the loop variable, so we try and locate
            # the host name in the delegated variable dictionary here
            delegated_vars = variables.get('ansible_delegated_vars', dict()).get(task.delegate_to, dict())

            delegated_transport = C.DEFAULT_TRANSPORT
            for transport_var in C.MAGIC_VARIABLE_MAPPING.get('connection'):
                if transport_var in delegated_vars:
                    delegated_transport = delegated_vars[transport_var]
                    break

            # make sure this delegated_to host has something set for its remote
            # address, otherwise we default to connecting to it by name. This
            # may happen when users put an IP entry into their inventory, or if
            # they rely on DNS for a non-inventory hostname
            for address_var in ('ansible_%s_host' % delegated_transport,) + C.MAGIC_VARIABLE_MAPPING.get('remote_addr'):
                if address_var in delegated_vars:
                    break
            else:
                display.debug("no remote address found for delegated host %s\nusing its name, so success depends on DNS resolution" % task.delegate_to)
                delegated_vars['ansible_host'] = task.delegate_to

            # reset the port back to the default if none was specified, to prevent
            # the delegated host from inheriting the original host's setting
            for port_var in ('ansible_%s_port' % delegated_transport,) + C.MAGIC_VARIABLE_MAPPING.get('port'):
                if port_var in delegated_vars:
                    break
            else:
                if delegated_transport == 'winrm':
                    delegated_vars['ansible_port'] = 5986
                else:
                    delegated_vars['ansible_port'] = C.DEFAULT_REMOTE_PORT

            # and likewise for the remote user
            for user_var in ('ansible_%s_user' % delegated_transport,) + C.MAGIC_VARIABLE_MAPPING.get('remote_user'):
                if user_var in delegated_vars and delegated_vars[user_var]:
                    break
            else:
                delegated_vars['ansible_user'] = task.remote_user or self.remote_user
        else:
            delegated_vars = dict()

            # setup shell
            for exe_var in C.MAGIC_VARIABLE_MAPPING.get('executable'):
                if exe_var in variables:
                    setattr(new_info, 'executable', variables.get(exe_var))

        attrs_considered = []
        for (attr, variable_names) in C.MAGIC_VARIABLE_MAPPING.items():
            for variable_name in variable_names:
                if attr in attrs_considered:
                    continue
                # if delegation task ONLY use delegated host vars, avoid delegated FOR host vars
                if task.delegate_to is not None:
                    if isinstance(delegated_vars, dict) and variable_name in delegated_vars:
                        setattr(new_info, attr, delegated_vars[variable_name])
                        attrs_considered.append(attr)
                elif variable_name in variables:
                    setattr(new_info, attr, variables[variable_name])
                    attrs_considered.append(attr)
                # no else, as no other vars should be considered

        # become legacy updates -- from inventory file (inventory overrides
        # commandline)
        for become_pass_name in C.MAGIC_VARIABLE_MAPPING.get('become_pass'):
            if become_pass_name in variables:
                break

        # make sure we get port defaults if needed
        if new_info.port is None and C.DEFAULT_REMOTE_PORT is not None:
            new_info.port = int(C.DEFAULT_REMOTE_PORT)

        # special overrides for the connection setting
        if len(delegated_vars) > 0:
            # in the event that we were using local before make sure to reset the
            # connection type to the default transport for the delegated-to host,
            # if not otherwise specified
            for connection_type in C.MAGIC_VARIABLE_MAPPING.get('connection'):
                if connection_type in delegated_vars:
                    break
            else:
                remote_addr_local = new_info.remote_addr in C.LOCALHOST
                inv_hostname_local = delegated_vars.get('inventory_hostname') in C.LOCALHOST
                if remote_addr_local and inv_hostname_local:
                    setattr(new_info, 'connection', 'local')
                elif getattr(new_info, 'connection', None) == 'local' and (not remote_addr_local or not inv_hostname_local):
                    setattr(new_info, 'connection', C.DEFAULT_TRANSPORT)

        # we store original in 'connection_user' for use of network/other modules that fallback to it as login user
        # connection_user to be deprecated once connection=local is removed for, as local resets remote_user
        if new_info.connection == 'local':
            if not new_info.connection_user:
                new_info.connection_user = new_info.remote_user

        # for case in which connection plugin still uses pc.remote_addr and in it's own options
        # specifies 'default: inventory_hostname', but never added to vars:
        if new_info.remote_addr == 'inventory_hostname':
            new_info.remote_addr = variables.get('inventory_hostname')
            display.warning('The "%s" connection plugin has an improperly configured remote target value, '
                            'forcing "inventory_hostname" templated value instead of the string' % new_info.connection)

        if task.check_mode is not None:
            new_info.check_mode = task.check_mode

        if task.diff is not None:
            new_info.diff = task.diff

        return new_info