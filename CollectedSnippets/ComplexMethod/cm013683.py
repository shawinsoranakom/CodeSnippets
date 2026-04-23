def __eq__(self, other: object) -> bool:
        if not isinstance(other, _MaskModWrapper):
            return False
        if self.fn is other.fn and self.closure_spec is other.closure_spec:
            return True
        # Extracted case: _StrippedClosure — compare code + closure_spec
        if isinstance(self.fn, _StrippedClosure) and isinstance(
            other.fn, _StrippedClosure
        ):
            return (
                self.fn.code == other.fn.code
                and self.closure_spec == other.closure_spec
            )
        # Non-extracted plain functions: compare code + closure contents
        if inspect.isfunction(self.fn) and inspect.isfunction(other.fn):
            return self.fn.__code__ == other.fn.__code__
        # Callable objects: delegate to their __eq__
        if not isinstance(self.fn, _StrippedClosure) and not isinstance(
            other.fn, _StrippedClosure
        ):
            return self.fn == other.fn
        return False