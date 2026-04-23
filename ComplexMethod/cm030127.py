def __mro_entries__(self, bases):
        res = []
        if self.__origin__ not in bases:
            res.append(self.__origin__)

        # Check if any base that occurs after us in `bases` is either itself a
        # subclass of Generic, or something which will add a subclass of Generic
        # to `__bases__` via its `__mro_entries__`. If not, add Generic
        # ourselves. The goal is to ensure that Generic (or a subclass) will
        # appear exactly once in the final bases tuple. If we let it appear
        # multiple times, we risk "can't form a consistent MRO" errors.
        i = bases.index(self)
        for b in bases[i+1:]:
            if isinstance(b, _BaseGenericAlias):
                break
            if not isinstance(b, type):
                meth = getattr(b, "__mro_entries__", None)
                new_bases = meth(bases) if meth else None
                if (
                    isinstance(new_bases, tuple) and
                    any(
                        isinstance(b2, type) and issubclass(b2, Generic)
                        for b2 in new_bases
                    )
                ):
                    break
            elif issubclass(b, Generic):
                break
        else:
            res.append(Generic)
        return tuple(res)