def __init__(self, verbose_name=None, srid=4326, spatial_index=True, **kwargs):
        """
        The initialization function for base spatial fields. Takes the
        following as keyword arguments:

        srid:
         The spatial reference system identifier, an OGC standard.
         Defaults to 4326 (WGS84).

        spatial_index:
         Indicates whether to create a spatial index. Defaults to True.
         Set this instead of 'db_index' for geographic fields since index
         creation is different for geometry columns.
        """

        # Setting the index flag with the value of the `spatial_index` keyword.
        self.spatial_index = spatial_index

        # Setting the SRID and getting the units. Unit information must be
        # easily available in the field instance for distance queries.
        self.srid = srid

        # Setting the verbose_name keyword argument with the positional
        # first parameter, so this works like normal fields.
        kwargs["verbose_name"] = verbose_name

        super().__init__(**kwargs)