def v2_method_expects_task_result(self, *args, method_name: str, **_kwargs) -> None:
        """Standard behavioral tests for callback methods accepting a task result; wired dynamically."""
        print(f'hello from {method_name}')
        result = self.get_first_task_result(args)

        assert result is self._current_task_result

        assert isinstance(result, CallbackTaskResult)

        assert result not in self.seen_tr

        self.seen_tr.append(result)

        has_exception = bool(result.exception)
        has_warnings = bool(result.warnings)
        has_deprecations = bool(result.deprecations)

        self._display.reset_mock()

        self._handle_exception(result.result)  # pops exception from transformed dict

        if has_exception:
            assert 'exception' not in result.result
            self._display._error.assert_called()

        self._display.reset_mock()

        self._handle_warnings(result.result)  # pops warnings/deprecations from transformed dict

        if has_warnings:
            assert 'warnings' not in result.result
            self._display._warning.assert_called()

        if has_deprecations:
            assert 'deprecations' not in result.result
            self._display._deprecated.assert_called()