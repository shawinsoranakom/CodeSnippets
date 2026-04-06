def _security_scheme(self) -> SecurityBase:
        unwrapped = _unwrapped_call(self.call)
        assert isinstance(unwrapped, SecurityBase)
        return unwrapped