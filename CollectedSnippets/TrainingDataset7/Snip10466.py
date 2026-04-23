def serialize(self):
        imports = set()
        # Avoid iterating self.value, because it returns itself.
        # https://github.com/python/cpython/issues/103450
        for item in self.value.__args__:
            _, item_imports = serializer_factory(item).serialize()
            imports.update(item_imports)
        return repr(self.value), imports