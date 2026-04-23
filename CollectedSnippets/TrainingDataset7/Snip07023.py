def __getitem__(self, index):
        "Get the Geometry at the specified index."
        if 0 <= index < self.geom_count:
            return OGRGeometry(
                capi.clone_geom(capi.get_geom_ref(self.ptr, index)), self.srs
            )
        else:
            raise IndexError(
                "Index out of range when accessing geometry in a collection: %s."
                % index
            )