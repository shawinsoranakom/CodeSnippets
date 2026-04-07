def hasm(self):
        """
        Return whether this coordinate sequence has M dimension.
        """
        if geos_version_tuple() >= (3, 14):
            return capi.cs_hasm(self._ptr)
        else:
            raise NotImplementedError(
                "GEOSCoordSeq with an M dimension requires GEOS 3.14+."
            )