def relate_pattern(self, other, pattern):
        """
        Return true if the elements in the DE-9IM intersection matrix for the
        two Geometries match the elements in pattern.
        """
        if not isinstance(pattern, str) or len(pattern) > 9:
            raise GEOSException("Invalid intersection matrix pattern.")
        return capi.geos_relatepattern(self.ptr, other.ptr, force_bytes(pattern))