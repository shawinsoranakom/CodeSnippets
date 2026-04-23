def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):

        ir = IncludeRole(block, role, task_include=task_include).load_data(data, variable_manager=variable_manager, loader=loader)

        # Validate options
        my_arg_names = frozenset(ir.args.keys())

        # name is needed, or use role as alias
        ir._role_name = ir.args.get('name', ir.args.get('role'))
        if ir._role_name is None:
            raise AnsibleParserError("'name' is a required field for %s." % ir.action, obj=data)

        # validate bad args, otherwise we silently ignore
        bad_opts = my_arg_names.difference(IncludeRole.VALID_ARGS)
        if bad_opts:
            raise AnsibleParserError('Invalid options for %s: %s' % (ir.action, ','.join(list(bad_opts))), obj=data)

        # build options for role include/import tasks
        for key in my_arg_names.intersection(IncludeRole.FROM_ARGS):
            from_key = key.removesuffix('_from')
            args_value = ir.args.get(key)
            if not isinstance(args_value, str):
                raise AnsibleParserError('Expected a string for %s but got %s instead' % (key, type(args_value)))
            ir._from_files[from_key] = args_value

        # apply and rescuable are only valid for includes, not imports as they inherit directly
        apply_attrs = ir.args.get('apply', {})
        if apply_attrs and ir.action not in C._ACTION_INCLUDE_ROLE:
            raise AnsibleParserError('Invalid options for %s: apply' % ir.action, obj=data)
        elif not isinstance(apply_attrs, dict):
            raise AnsibleParserError('Expected a dict for apply but got %s instead' % type(apply_attrs), obj=data)

        resc_attr = ir.args.get('rescuable', None)
        if resc_attr and ir.action not in C._ACTION_INCLUDE_ROLE:
            raise AnsibleParserError(f'Invalid options for {ir.action}: rescuable', obj=data)

        # manual list as otherwise the options would set other task parameters we don't want.
        for option in my_arg_names.intersection(IncludeRole.OTHER_ARGS):
            setattr(ir, option, ir.args.get(option))

        return ir