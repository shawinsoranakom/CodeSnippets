def __init__(
        self,
        verbose_name=None,
        dim=2,
        geography=False,
        *,
        extent=(-180.0, -90.0, 180.0, 90.0),
        tolerance=0.05,
        **kwargs,
    ):
        """
        The initialization function for geometry fields. In addition to the
        parameters from BaseSpatialField, it takes the following as keyword
        arguments:

        dim:
         The number of dimensions for this geometry. Defaults to 2.

        extent:
         Customize the extent, in a 4-tuple of WGS 84 coordinates, for the
         geometry field entry in the `USER_SDO_GEOM_METADATA` table. Defaults
         to (-180.0, -90.0, 180.0, 90.0).

        tolerance:
         Define the tolerance, in meters, to use for the geometry field
         entry in the `USER_SDO_GEOM_METADATA` table. Defaults to 0.05.
        """
        # Setting the dimension of the geometry field.
        self.dim = dim

        # Is this a geography rather than a geometry column?
        self.geography = geography

        # Oracle-specific private attributes for creating the entry in
        # `USER_SDO_GEOM_METADATA`
        self._extent = extent
        self._tolerance = tolerance

        super().__init__(verbose_name=verbose_name, **kwargs)