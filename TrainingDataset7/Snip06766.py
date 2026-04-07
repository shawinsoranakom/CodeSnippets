def get_srid(self, obj):
        """
        Return the default SRID for the given geometry or raster, taking into
        account the SRID set for the field. For example, if the input geometry
        or raster doesn't have an SRID, then the SRID of the field will be
        returned.
        """
        srid = obj.srid  # SRID of given geometry.
        if srid is None or self.srid == -1 or (srid == -1 and self.srid != -1):
            return self.srid
        else:
            return srid