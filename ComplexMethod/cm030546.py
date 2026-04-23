def fixtype(self, obj):
        if isinstance(obj, str):
            return self.__class__.type2test(obj)
        elif isinstance(obj, list):
            return [self.fixtype(x) for x in obj]
        elif isinstance(obj, tuple):
            return tuple([self.fixtype(x) for x in obj])
        elif isinstance(obj, dict):
            return dict([
               (self.fixtype(key), self.fixtype(value))
               for (key, value) in obj.items()
            ])
        else:
            return obj