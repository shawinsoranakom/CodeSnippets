def plural(self, msgid, num):
        for cat, plural in zip(self._catalogs, self._plurals):
            tmsg = cat.get((msgid, plural(num)))
            if tmsg is not None:
                return tmsg
        raise KeyError