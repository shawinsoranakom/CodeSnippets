def make_multi(self, geom_type, model_field):
        """
        Given the OGRGeomType for a geometry and its associated GeometryField,
        determine whether the geometry should be turned into a
        GeometryCollection.
        """
        return (
            geom_type.num in self.MULTI_TYPES
            and model_field.__class__.__name__ == "Multi%s" % geom_type.django
        )