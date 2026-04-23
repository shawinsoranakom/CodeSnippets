def assertSameResult(
        self,
        expected: Callable[[], Any],
        actual: Callable[[], Any],
        *args,
        **kwargs,
    ) -> None:
        try:
            result_e = expected()
            exception_e = None
        except Exception as e:
            result_e = None
            exception_e = e

        try:
            result_a = actual()
            exception_a = None
        except Exception as e:
            result_a = None
            exception_a = e

        if (exception_e is None) != (exception_a is None):
            if exception_a is not None and exception_e is None:
                raise exception_a
            self.assertIs(
                type(exception_e),
                type(exception_a),
                f"\n{exception_e=}\n{exception_a=}",
            )

        if exception_e is None:
            flattened_e, spec_e = tree_flatten(result_e)
            flattened_a, spec_a = tree_flatten(result_a)

            self.assertEqual(
                spec_e,
                spec_a,
                "Both functions must return a result with the same tree structure.",
            )
            for value_e, value_a in zip(flattened_e, flattened_a, strict=True):
                value_e = _as_interleaved(_as_local(value_e))
                value_a = _as_interleaved(_as_local(value_a))

                self.assertEqual(value_e, value_a, *args, **kwargs)