def original_dec(wrapped):
            def _wrapped(arg):
                return wrapped(arg)

            return _wrapped