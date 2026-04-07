def _set_srid(self, srid):
        if isinstance(srid, int) or srid is None:
            self.srs = srid
        else:
            raise TypeError("SRID must be set with an integer.")