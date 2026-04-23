def _assertFooMessage(
        self, func, cm_attr, expected_exception, expected_message, *args, **kwargs
    ):
        callable_obj = None
        if args:
            callable_obj, *args = args
        cm = self._assert_raises_or_warns_cm(
            func, cm_attr, expected_exception, expected_message
        )
        # Assertion used in context manager fashion.
        if callable_obj is None:
            return cm
        # Assertion was passed a callable.
        with cm:
            callable_obj(*args, **kwargs)