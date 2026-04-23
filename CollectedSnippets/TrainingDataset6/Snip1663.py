def is_coroutine_callable(self) -> bool:
        if self.call is None:
            return False  # pragma: no cover
        if inspect.isroutine(_impartial(self.call)) and iscoroutinefunction(
            _impartial(self.call)
        ):
            return True
        if inspect.isroutine(_unwrapped_call(self.call)) and iscoroutinefunction(
            _unwrapped_call(self.call)
        ):
            return True
        if inspect.isclass(_unwrapped_call(self.call)):
            return False
        dunder_call = getattr(_impartial(self.call), "__call__", None)  # noqa: B004
        if dunder_call is None:
            return False  # pragma: no cover
        if iscoroutinefunction(_impartial(dunder_call)) or iscoroutinefunction(
            _unwrapped_call(dunder_call)
        ):
            return True
        dunder_unwrapped_call = getattr(_unwrapped_call(self.call), "__call__", None)  # noqa: B004
        if dunder_unwrapped_call is None:
            return False  # pragma: no cover
        if iscoroutinefunction(
            _impartial(dunder_unwrapped_call)
        ) or iscoroutinefunction(_unwrapped_call(dunder_unwrapped_call)):
            return True
        return False