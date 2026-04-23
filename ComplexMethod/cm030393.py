def assert_has_calls(self, calls, any_order=False):
        """assert the mock has been called with the specified calls.
        The `mock_calls` list is checked for the calls.

        If `any_order` is False (the default) then the calls must be
        sequential. There can be extra calls before or after the
        specified calls.

        If `any_order` is True then the calls can be in any order, but
        they must all appear in `mock_calls`."""
        expected = [self._call_matcher(c) for c in calls]
        cause = next((e for e in expected if isinstance(e, Exception)), None)
        all_calls = _CallList(self._call_matcher(c) for c in self.mock_calls)
        if not any_order:
            if expected not in all_calls:
                if cause is None:
                    problem = 'Calls not found.'
                else:
                    problem = ('Error processing expected calls.\n'
                               'Errors: {}').format(
                                   [e if isinstance(e, Exception) else None
                                    for e in expected])
                raise AssertionError(
                    f'{problem}\n'
                    f'Expected: {_CallList(calls)}\n'
                    f'  Actual: {safe_repr(self.mock_calls)}'
                ) from cause
            return

        all_calls = list(all_calls)

        not_found = []
        for kall in expected:
            try:
                all_calls.remove(kall)
            except ValueError:
                not_found.append(kall)
        if not_found:
            raise AssertionError(
                '%r does not contain all of %r in its call list, '
                'found %r instead' % (self._mock_name or 'mock',
                                      tuple(not_found), all_calls)
            ) from cause