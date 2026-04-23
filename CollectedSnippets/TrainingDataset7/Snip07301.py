def ewkt(self):
        """
        Return the EWKT (SRID + WKT) of the Geometry.
        """
        srid = self.srid
        return "SRID=%s;%s" % (srid, self.wkt) if srid else self.wkt