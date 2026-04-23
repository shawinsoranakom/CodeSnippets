def _to_pickle_wkb(self):
        return None if self.empty else super()._to_pickle_wkb()