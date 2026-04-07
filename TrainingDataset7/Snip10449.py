def serialize(self):
        imports = set()
        strings = []
        for item in self.value:
            item_string, item_imports = serializer_factory(item).serialize()
            imports.update(item_imports)
            strings.append(item_string)
        value = self._format()
        return value % (", ".join(strings)), imports