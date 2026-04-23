def hex(self):
        """
        Return the WKB of this Geometry in hexadecimal form. Please note
        that the SRID is not included in this representation because it is not
        a part of the OGC specification (use the `hexewkb` property instead).
        """
        # A possible faster, all-python, implementation:
        #  str(self.wkb).encode('hex')
        return wkb_w(dim=3 if self.hasz else 2).write_hex(self)