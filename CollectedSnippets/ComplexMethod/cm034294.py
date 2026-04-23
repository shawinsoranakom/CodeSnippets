def __setattr__(self, name, value):
        if name.startswith('_self_'):
            object.__setattr__(self, name, value)

        elif name == '__wrapped__':
            object.__setattr__(self, name, value)
            try:
                object.__delattr__(self, '__qualname__')
            except AttributeError:
                pass
            try:
                object.__setattr__(self, '__qualname__', value.__qualname__)
            except AttributeError:
                pass
            try:
                object.__delattr__(self, '__annotations__')
            except AttributeError:
                pass
            try:
                object.__setattr__(self, '__annotations__', value.__annotations__)
            except AttributeError:
                pass

        elif name == '__qualname__':
            setattr(self.__wrapped__, name, value)
            object.__setattr__(self, name, value)

        elif name == '__annotations__':
            setattr(self.__wrapped__, name, value)
            object.__setattr__(self, name, value)

        elif hasattr(type(self), name):
            object.__setattr__(self, name, value)

        else:
            setattr(self.__wrapped__, name, value)