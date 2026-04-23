def __wrapper__(self, *args, __method_name=method_name, **kw):
                    # Automatically triggers the evaluation of a lazy value and
                    # applies the given method of the result type.
                    result = func(*self._args, **self._kw)
                    return getattr(result, __method_name)(*args, **kw)