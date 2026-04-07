def __get__(self, instance, cls=None):
        """
        Retrieve the geometry or raster, initializing it using the
        corresponding class specified during initialization and the value of
        the field. Currently, GEOS or OGR geometries as well as GDALRasters are
        supported.
        """
        if instance is None:
            # Accessed on a class, not an instance
            return self

        # Getting the value of the field.
        try:
            geo_value = instance.__dict__[self.field.attname]
        except KeyError:
            geo_value = super().__get__(instance, cls)

        if isinstance(geo_value, self._klass):
            geo_obj = geo_value
        elif (geo_value is None) or (geo_value == ""):
            geo_obj = None
        else:
            # Otherwise, a geometry or raster object is built using the field's
            # contents, and the model's corresponding attribute is set.
            geo_obj = self._load_func(geo_value)
            setattr(instance, self.field.attname, geo_obj)
        return geo_obj