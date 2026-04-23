def to_python(self, value):
        """Transform the value to a Geometry object."""
        if value in self.empty_values:
            return None

        if not isinstance(value, GEOSGeometry):
            if hasattr(self.widget, "deserialize"):
                value = self.widget.deserialize(value)
            else:
                try:
                    value = GEOSGeometry(value)
                except (GEOSException, ValueError, TypeError):
                    value = None
            if value is None:
                raise ValidationError(
                    self.error_messages["invalid_geom"], code="invalid_geom"
                )

        # Try to set the srid
        if not value.srid:
            try:
                value.srid = self.widget.map_srid
            except AttributeError:
                if self.srid:
                    value.srid = self.srid
        return value