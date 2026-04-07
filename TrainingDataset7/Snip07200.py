def _create_collection(self, length, items):
        # Creating the geometry pointer array.
        geoms = (GEOM_PTR * length)(
            *[
                # this is a little sloppy, but makes life easier
                # allow GEOSGeometry types (python wrappers) or pointer types
                capi.geom_clone(getattr(g, "ptr", g))
                for g in items
            ]
        )
        return capi.create_collection(self._typeid, geoms, length)