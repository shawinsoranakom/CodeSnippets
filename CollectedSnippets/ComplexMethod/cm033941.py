def run(self, tmp=None, task_vars=None):

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        args = self._task.args
        raw = args.pop('_raw_params', {})
        if isinstance(raw, Mapping):
            # TODO: create 'conflict' detection in base class to deal with repeats and aliases and warn user
            args = combine_vars(raw, args)
        else:
            raise AnsibleActionFail('Invalid raw parameters passed, requires a dictionary/mapping got a  %s' % type(raw))

        # Parse out any hostname:port patterns
        new_name = args.get('name', args.get('hostname', args.get('host', None)))
        if new_name is None:
            raise AnsibleActionFail('name, host or hostname needs to be provided')

        display.vv("creating host via 'add_host': hostname=%s" % new_name)

        try:
            name, port = parse_address(new_name, allow_ranges=False)
        except Exception:
            # not a parsable hostname, but might still be usable
            name = new_name
            port = None

        if port:
            args['ansible_ssh_port'] = port

        groups = args.get('groupname', args.get('groups', args.get('group', '')))
        # add it to the group if that was specified
        new_groups = []
        if groups:
            if isinstance(groups, list):
                group_list = groups
            elif isinstance(groups, str):
                group_list = groups.split(",")
            else:
                raise AnsibleActionFail("Groups must be specified as a list.", obj=groups)

            for group_name in group_list:
                if group_name not in new_groups:
                    new_groups.append(group_name.strip())

        # Add any variables to the new_host
        host_vars = dict()
        special_args = frozenset(('name', 'hostname', 'groupname', 'groups'))
        for k in args.keys():
            if k not in special_args:
                host_vars[k] = args[k]

        result['add_host'] = dict(host_name=name, groups=new_groups, host_vars=host_vars)
        result['changed'] = self.add_host(host_name=name, parent_group_names=new_groups, host_vars=host_vars)

        return result