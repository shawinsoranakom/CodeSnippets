def ewkb(self):
        """
        Return the EWKB representation of this Geometry as a Python memoryview.
        This is an extension of the WKB specification that includes any SRID
        value that are a part of this geometry.
        """
        return ewkb_w(3 if self.hasz else 2).write(self)