def __setattr__(self, name, value):
        if name == 'prec':
            return self._set_integer_check(name, value, 1, 'inf')
        elif name == 'Emin':
            return self._set_integer_check(name, value, '-inf', 0)
        elif name == 'Emax':
            return self._set_integer_check(name, value, 0, 'inf')
        elif name == 'capitals':
            return self._set_integer_check(name, value, 0, 1)
        elif name == 'clamp':
            return self._set_integer_check(name, value, 0, 1)
        elif name == 'rounding':
            if not value in _rounding_modes:
                # raise TypeError even for strings to have consistency
                # among various implementations.
                raise TypeError("%s: invalid rounding mode" % value)
            return object.__setattr__(self, name, value)
        elif name == 'flags' or name == 'traps':
            return self._set_signal_dict(name, value)
        elif name == '_ignored_flags':
            return object.__setattr__(self, name, value)
        else:
            raise AttributeError(
                "'decimal.Context' object has no attribute '%s'" % name)