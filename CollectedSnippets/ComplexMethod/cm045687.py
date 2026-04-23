def resolve(self, obj: object) -> object:
        if id(obj) in self.done:
            return obj

        match obj:
            case Variable() as v:
                return self.resolve_variable(v)
            case Value(constructed=True, value=value):
                return value
            case Value(constructor=constructor, kwargs=kwargs) as v:
                resolved_kwargs = self.resolve(kwargs)
                assert constructor is not None
                obj = constructor(**resolved_kwargs)
                v.constructed = True
                v.value = obj
            case dict() as d:
                context = {}
                variables = list(v for v in d.keys() if isinstance(v, Variable))
                if variables:
                    for v in variables:
                        context[v] = d.pop(v)
                    with self.subresolver(context) as resolver:
                        return resolver.resolve(d)
                for key, value in d.items():
                    d[key] = self.resolve(value)
            case list() as ls:
                for index, value in enumerate(ls):
                    ls[index] = self.resolve(value)

        self.done[id(obj)] = obj
        return obj