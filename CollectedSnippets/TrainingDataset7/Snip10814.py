def identity(self):
        args, kwargs = self._constructor_args
        signature = self._constructor_signature.bind_partial(self, *args, **kwargs)
        signature.apply_defaults()
        arguments = iter(signature.arguments.items())
        next(arguments)
        identity = [self.__class__]
        for arg, value in arguments:
            # If __init__() makes use of *args or **kwargs captures `value`
            # will respectively be a tuple or a dict that must have its
            # constituents unpacked (mainly if contain Field instances).
            value = self._identity(value)
            identity.append((arg, value))
        return tuple(identity)