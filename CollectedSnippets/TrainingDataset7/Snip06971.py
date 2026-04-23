def _get_srid(self):
        srs = self.srs
        if srs:
            return srs.srid
        return None