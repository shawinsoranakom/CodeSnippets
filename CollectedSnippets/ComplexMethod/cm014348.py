def patch(
        self,
        arg1: str | dict[str, Any] | None = None,
        arg2: Any = None,
        **kwargs: dict[str, Any],
    ) -> "ContextDecorator":
        """
        Decorator and/or context manager to make temporary changes to a config.  Note that patched settings are thread-local.

        As a decorator:

            @config.patch("name", val)
            @config.patch(name1=val1, name2=val2)
            @config.patch({"name1": val1, "name2", val2})
            def foo(...):
                ...

        As a context manager:

            with config.patch("name", val):
                ...
        """
        changes: dict[str, Any]
        if arg1 is not None:
            if arg2 is not None:
                if not isinstance(arg1, str):
                    raise AssertionError(
                        "first argument must be a string when passing 2 positional args to patch"
                    )
                # patch("key", True) syntax
                changes = {arg1: arg2}
            else:
                if not isinstance(arg1, dict):
                    raise AssertionError(
                        "first argument must be a dict when passing a single positional arg to patch"
                    )
                # patch({"key": True}) syntax
                changes = arg1
            if kwargs:
                raise AssertionError(
                    "cannot pass both positional and keyword arguments to patch"
                )
        else:
            # patch(key=True) syntax
            changes = kwargs
            if arg2 is not None:
                raise AssertionError(
                    "second positional argument is only valid when first argument is a key string"
                )
        if not isinstance(changes, dict):
            raise AssertionError(f"expected `dict` got {type(changes)}")
        config = self

        class ConfigPatch(ContextDecorator):
            def __init__(self) -> None:
                self.changes = changes
                self._prior: ContextVar[tuple[dict[str, Any], ...]] = ContextVar(
                    f"{config.__name__}.ConfigPatch[{id(self)}]",
                    default=(),
                )

            def __enter__(self) -> None:
                prior: dict[str, Any] = {}
                for key in self.changes:
                    # KeyError on invalid entry
                    prior[key] = config.__getattr__(key)
                prior_stack = self._prior.get()
                self._prior.set((*prior_stack, prior))
                try:
                    for k, v in self.changes.items():
                        config.__setattr__(k, v)
                except Exception:
                    self._prior.set(prior_stack)
                    raise

            def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore[no-untyped-def]
                prior_stack = self._prior.get()
                if not prior_stack:
                    raise AssertionError(
                        "prior should not be empty when exiting ConfigPatch"
                    )
                prior = prior_stack[-1]
                self._prior.set(prior_stack[:-1])
                for k, v in prior.items():
                    config.__setattr__(k, v)

        return ConfigPatch()