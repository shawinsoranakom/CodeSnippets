def __copy__(self):
        """
        Return a clone because the copy of a GEOSGeometry may contain an
        invalid pointer location if the original is garbage collected.
        """
        return self.clone()