def clean(self, value):
        """
        Validate that the input value can be converted to a Geometry object
        and return it. Raise a ValidationError if the value cannot be
        instantiated as a Geometry.
        """
        geom = super().clean(value)
        if geom is None:
            return geom

        # Ensuring that the geometry is of the correct type (indicated
        # using the OGC string label).
        if (
            str(geom.geom_type).upper() != self.geom_type
            and self.geom_type != "GEOMETRY"
        ):
            raise ValidationError(
                self.error_messages["invalid_geom_type"], code="invalid_geom_type"
            )

        # Transforming the geometry if the SRID was set.
        if self.srid and self.srid != -1 and self.srid != geom.srid:
            try:
                geom.transform(self.srid)
            except GEOSException:
                raise ValidationError(
                    self.error_messages["transform_error"], code="transform_error"
                )

        return geom