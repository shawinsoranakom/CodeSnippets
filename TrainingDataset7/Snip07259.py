def __getstate__(self):
        # The pickled state is simply a tuple of the WKB (in string form)
        # and the SRID.
        return self._to_pickle_wkb(), self.srid