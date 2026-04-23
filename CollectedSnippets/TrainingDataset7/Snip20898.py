def _inner(*args, **kwargs):
        result = functions[0](*args, **kwargs)
        for f in functions[1:]:
            result = f(result)
        return result