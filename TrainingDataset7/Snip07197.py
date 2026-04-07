def __init__(self, *args, **kwargs):
        "Initialize a Geometry Collection from a sequence of Geometry objects."
        # Checking the arguments
        if len(args) == 1:
            # If only one geometry provided or a list of geometries is provided
            #  in the first argument.
            if isinstance(args[0], (tuple, list)):
                init_geoms = args[0]
            else:
                init_geoms = args
        else:
            init_geoms = args

        # Ensuring that only the permitted geometries are allowed in this
        # collection this is moved to list mixin super class
        self._check_allowed(init_geoms)

        # Creating the geometry pointer array.
        collection = self._create_collection(len(init_geoms), init_geoms)
        super().__init__(collection, **kwargs)