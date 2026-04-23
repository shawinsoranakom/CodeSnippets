def identity(self):
        path, args, kwargs = self.deconstruct()
        identity = [path, *kwargs.items()]
        for child in args:
            if isinstance(child, tuple):
                arg, value = child
                value = make_hashable(value)
                identity.append((arg, value))
            else:
                identity.append(child)
        return tuple(identity)