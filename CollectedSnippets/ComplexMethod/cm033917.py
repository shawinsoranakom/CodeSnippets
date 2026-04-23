def run(self, tmp: str | None = None, task_vars: dict[str, t.Any] | None = None) -> dict[str, t.Any]:
        """ Action Plugins should implement this method to perform their
        tasks.  Everything else in this base class is a helper method for the
        action plugin to do that.

        :kwarg tmp: Deprecated parameter.  This is no longer used.  An action plugin that calls
            another one and wants to use the same remote tmp for both should set
            self._connection._shell.tmpdir rather than this parameter.
        :kwarg task_vars: The variables (host vars, group vars, config vars,
            etc) associated with this task.
        :returns: dictionary of results from the module

        Implementers of action modules may find the following variables especially useful:

        * Module parameters.  These are stored in self._task.args
        """
        # does not default to {'changed': False, 'failed': False}, as it used to break async
        result: dict[str, t.Any] = {}

        if tmp is not None:
            display.warning('ActionModule.run() no longer honors the tmp parameter. Action'
                            ' plugins should set self._connection._shell.tmpdir to share'
                            ' the tmpdir.')
        del tmp

        if self._task.async_val and not self._supports_async:
            raise AnsibleActionFail('This action (%s) does not support async.' % self._task.action)
        elif self._task.check_mode and not self._supports_check_mode:
            raise AnsibleActionSkip('This action (%s) does not support check mode.' % self._task.action)

        # Error if invalid argument is passed
        if self._VALID_ARGS:
            task_opts = frozenset(self._task.args.keys())
            bad_opts = task_opts.difference(self._VALID_ARGS)
            if bad_opts:
                raise AnsibleActionFail('Invalid options for %s: %s' % (self._task.action, ','.join(list(bad_opts))))

        if self._connection._shell.tmpdir is None and self._early_needs_tmp_path():
            self._make_tmp_path()

        return result