def _from_wkb(cls, geom_input):
        return capi.from_wkb(
            bytes(geom_input), None, byref(c_void_p()), len(geom_input)
        )