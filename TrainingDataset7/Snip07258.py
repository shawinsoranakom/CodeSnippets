def _from_pickle_wkb(self, wkb):
        return wkb_r().read(memoryview(wkb))