def _handle_warnings(self, res: _c.MutableMapping[str, t.Any]) -> None:
        """Display warnings and deprecation warnings sourced by task execution."""
        if res.pop('warnings', None) and self._current_task_result and (warnings := self._current_task_result.warnings):
            # display warnings from the current task result if `warnings` was not removed from `result` (or made falsey)
            for warning in warnings:
                self._display._warning(warning)

        if res.pop('deprecations', None) and self._current_task_result and (deprecations := self._current_task_result.deprecations):
            # display deprecations from the current task result if `deprecations` was not removed from `result` (or made falsey)
            for deprecation in deprecations:
                self._display._deprecated(deprecation)