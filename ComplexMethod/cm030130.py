def __getitem__(self, params):
        if not isinstance(params, tuple):
            params = (params,)
        msg = "Parameters to generic types must be types."
        params = tuple(_type_check(p, msg) for p in params)
        if (self._defaults
            and len(params) < self._nparams
            and len(params) + len(self._defaults) >= self._nparams
        ):
            params = (*params, *self._defaults[len(params) - self._nparams:])
        actual_len = len(params)

        if actual_len != self._nparams:
            if self._defaults:
                expected = f"at least {self._nparams - len(self._defaults)}"
            else:
                expected = str(self._nparams)
            if not self._nparams:
                raise TypeError(f"{self} is not a generic class")
            raise TypeError(f"Too {'many' if actual_len > self._nparams else 'few'} arguments for {self};"
                            f" actual {actual_len}, expected {expected}")
        return self.copy_with(params)