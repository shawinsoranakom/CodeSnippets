def _get_module_args(self, fact_module: str, task_vars: dict[str, t.Any]) -> dict[str, t.Any]:

        mod_args = self._task.args.copy()

        # deal with 'setup specific arguments'
        if fact_module not in C._ACTION_SETUP:

            # TODO: remove in favor of controller side argspec detecting valid arguments
            # network facts modules must support gather_subset
            name = self._connection.ansible_name.removeprefix('ansible.netcommon.')

            if name not in ('network_cli', 'httpapi', 'netconf'):
                subset = mod_args.pop('gather_subset', None)
                if subset not in ('all', ['all'], None):
                    self._display.warning('Not passing subset(%s) to %s' % (subset, fact_module))

            timeout = mod_args.pop('gather_timeout', None)
            if timeout is not None:
                self._display.warning('Not passing timeout(%s) to %s' % (timeout, fact_module))

            fact_filter = mod_args.pop('filter', None)
            if fact_filter is not None:
                self._display.warning('Not passing filter(%s) to %s' % (fact_filter, fact_module))

        # Strip out keys with ``None`` values, effectively mimicking ``omit`` behavior
        # This ensures we don't pass a ``None`` value as an argument expecting a specific type
        mod_args = dict((k, v) for k, v in mod_args.items() if v is not None)

        # handle module defaults
        resolved_fact_module = self._shared_loader_obj.module_loader.find_plugin_with_context(
            fact_module, collection_list=self._task.collections
        ).resolved_fqcn

        mod_args = _apply_action_arg_defaults(resolved_fact_module, self._task, mod_args, self._templar)

        return mod_args