def __init__(self, source, target):
        "Initialize on a source and target SpatialReference objects."
        if not isinstance(source, SpatialReference) or not isinstance(
            target, SpatialReference
        ):
            raise TypeError("source and target must be of type SpatialReference")
        self.ptr = capi.new_ct(source._ptr, target._ptr)
        self._srs1_name = source.name
        self._srs2_name = target.name