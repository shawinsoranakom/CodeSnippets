def call_function(
        self,
        fn: VariableTracker,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> None:
        assert isinstance(fn, VariableTracker)
        assert isinstance(args, list)
        assert isinstance(kwargs, dict)
        assert all(
            isinstance(x, VariableTracker)
            for x in itertools.chain(args, kwargs.values())
        )
        inner_fn = None
        if hasattr(fn, "value"):
            inner_fn = fn.value
        if hasattr(fn, "fn"):
            inner_fn = fn.fn
        if inner_fn and callable(inner_fn) and is_forbidden(inner_fn):
            raise AssertionError(f"Attempt to trace forbidden callable {inner_fn}")
        self.push(fn.call_function(self, args, kwargs))