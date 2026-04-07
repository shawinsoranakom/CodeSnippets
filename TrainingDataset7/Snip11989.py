def values(self, *fields, **expressions):
        fields += tuple(expressions)
        clone = self._values(*fields, **expressions)
        clone._iterable_class = ValuesIterable
        return clone