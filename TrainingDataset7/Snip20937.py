def deco(func):
            def _wrapper(*args, **kwargs):
                return True

            return _wrapper