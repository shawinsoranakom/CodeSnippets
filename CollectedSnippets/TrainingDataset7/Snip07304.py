def hexewkb(self):
        """
        Return the EWKB of this Geometry in hexadecimal form. This is an
        extension of the WKB specification that includes SRID value that are
        a part of this geometry.
        """
        return ewkb_w(dim=3 if self.hasz else 2).write_hex(self)