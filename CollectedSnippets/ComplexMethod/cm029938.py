def __dir__(self):
        """
        Returns public methods and other interesting attributes.
        """
        interesting = set()
        if self.__class__._member_type_ is not object:
            interesting = set(object.__dir__(self))
        for name in getattr(self, '__dict__', []):
            if name[0] != '_' and name not in self._member_map_:
                interesting.add(name)
        for cls in self.__class__.mro():
            for name, obj in cls.__dict__.items():
                if name[0] == '_':
                    continue
                if isinstance(obj, property):
                    # that's an enum.property
                    if obj.fget is not None or name not in self._member_map_:
                        interesting.add(name)
                    else:
                        # in case it was added by `dir(self)`
                        interesting.discard(name)
                elif name not in self._member_map_:
                    interesting.add(name)
        names = sorted(
                set(['__class__', '__doc__', '__eq__', '__hash__', '__module__'])
                | interesting
                )
        return names