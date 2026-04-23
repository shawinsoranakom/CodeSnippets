def __getstate__(self):
        srs = self.srs
        if srs:
            srs = srs.wkt
        else:
            srs = None
        return bytes(self.wkb), srs