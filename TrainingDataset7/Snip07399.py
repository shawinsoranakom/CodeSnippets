def _from_pickle_wkb(self, wkb):
        return self._create_empty() if wkb is None else super()._from_pickle_wkb(wkb)