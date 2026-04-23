def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        key: tuple[object, ...]
        if kwargs:
            kwargs = {k: v.realize() for k, v in kwargs.items()}
            key = (self.fn, *(type(x) for x in args), True)
        else:
            key = (self.fn, *(type(x) for x in args))

        handler = self.call_function_handler_cache.get(key)
        if not handler:
            self.call_function_handler_cache[key] = handler = self._make_handler(  # type: ignore[assignment]
                self.fn, [type(x) for x in args], bool(kwargs)
            )
        assert handler is not None
        return handler(tx, args, kwargs)