def update(self, trans):
        # Merge if plural function is the same as the top catalog, else
        # prepend.
        if trans.plural.__code__ == self._plurals[0]:
            self._catalogs[0].update(trans._catalog)
        else:
            self._catalogs.insert(0, trans._catalog.copy())
            self._plurals.insert(0, trans.plural)