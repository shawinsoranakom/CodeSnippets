def items(self):
        for cat in self._catalogs:
            yield from cat.items()