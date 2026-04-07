def ewkt(self):
        "Return the EWKT representation of the Geometry."
        srs = self.srs
        if srs and srs.srid:
            return "SRID=%s;%s" % (srs.srid, self.wkt)
        else:
            return self.wkt