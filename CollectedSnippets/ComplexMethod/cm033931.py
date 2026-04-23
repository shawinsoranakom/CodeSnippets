def _ensure_invocation(self, result: dict[str, _t.Any], task_vars: dict[str, _t.Any] | None = None) -> dict[str, _t.Any]:
        # NOTE: adding invocation arguments here needs to be kept in sync with
        # any no_log specified in the argument_spec in the module.
        # This is not automatic.
        # NOTE: do not add to this. This should be made a generic function for action plugins.
        # This should also use the same argspec as the module instead of keeping it in sync.
        if not C.config.get_config_value('INJECT_INVOCATION', variables=task_vars or {}, templar=self._templar):
            result.pop('invocation', None)
            return result

        if 'invocation' not in result:
            if self._task.no_log:
                result['invocation'] = "CENSORED: no_log is set"
            else:
                # NOTE: Should be removed in the future. For now keep this broken
                # behaviour, have a look in the PR 51582
                result['invocation'] = self._task.args.copy()
                result['invocation']['module_args'] = self._task.args.copy()

        if isinstance(result['invocation'], dict):
            if 'content' in result['invocation']:
                result['invocation']['content'] = 'CENSORED: content is a no_log parameter'
            if result['invocation'].get('module_args', {}).get('content') is not None:
                result['invocation']['module_args']['content'] = 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'

        return result