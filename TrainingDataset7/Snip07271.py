def coord_seq(self):
        "Return a clone of the coordinate sequence for this Geometry."
        if self.has_cs:
            return self._cs.clone()