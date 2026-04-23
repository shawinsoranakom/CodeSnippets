def wkb(self):
        """
        Return the WKB (Well-Known Binary) representation of this Geometry
        as a Python memoryview. SRID and Z values are not included, use the
        `ewkb` property instead.
        """
        return wkb_w(3 if self.hasz else 2).write(self)