def __init__(self, ptr, z=False):
        "Initialize from a GEOS pointer."
        # TODO when dropping support for GEOS 3.13 the z argument can be
        # deprecated in favor of using the GEOS function GEOSCoordSeq_hasZ.
        if not isinstance(ptr, CS_PTR):
            raise TypeError("Coordinate sequence should initialize with a CS_PTR.")
        self._ptr = ptr
        self._z = z