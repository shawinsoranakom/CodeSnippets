def __mro_entries__(self, bases):
        if isinstance(self.__origin__, _SpecialForm):
            raise TypeError(f"Cannot subclass {self!r}")

        if self._name:  # generic version of an ABC or built-in class
            return super().__mro_entries__(bases)
        if self.__origin__ is Generic:
            if Protocol in bases:
                return ()
            i = bases.index(self)
            for b in bases[i+1:]:
                if isinstance(b, _BaseGenericAlias) and b is not self:
                    return ()
        return (self.__origin__,)