def test_wrap_callable_instance(self):
        """#20028 -- Atomic must support wrapping callable instances."""

        class Callable:
            def __call__(self):
                pass

        # Must not raise an exception
        transaction.atomic(Callable())