def __init__(self, *args, **kwargs):
        """
        Initialize on the given sequence: may take lists, tuples, NumPy arrays
        of X,Y pairs, or Point objects. If Point objects are used, ownership is
        _not_ transferred to the LineString object.

        Examples:
         ls = LineString((1, 1), (2, 2))
         ls = LineString([(1, 1), (2, 2)])
         ls = LineString(array([(1, 1), (2, 2)]))
         ls = LineString(Point(1, 1), Point(2, 2))
        """
        # If only one argument provided, set the coords array appropriately
        if len(args) == 1:
            coords = args[0]
        else:
            coords = args

        if not (
            isinstance(coords, (tuple, list))
            or numpy
            and isinstance(coords, numpy.ndarray)
        ):
            raise TypeError("Invalid initialization input for LineStrings.")

        # If SRID was passed in with the keyword arguments
        srid = kwargs.get("srid")

        ncoords = len(coords)
        if not ncoords:
            super().__init__(self._init_func(None), srid=srid)
            return

        if ncoords < self._minlength:
            raise ValueError(
                "%s requires at least %d points, got %s."
                % (
                    self.__class__.__name__,
                    self._minlength,
                    ncoords,
                )
            )

        numpy_coords = not isinstance(coords, (tuple, list))
        if numpy_coords:
            shape = coords.shape  # Using numpy's shape.
            if len(shape) != 2:
                raise TypeError("Too many dimensions.")
            self._checkdim(shape[1])
            ndim = shape[1]
        else:
            # Getting the number of coords and the number of dimensions, which
            #  must stay the same, e.g., no LineString((1, 2), (1, 2, 3)).
            ndim = None
            # Incrementing through each of the coordinates and verifying
            for coord in coords:
                if not isinstance(coord, (tuple, list, Point)):
                    raise TypeError(
                        "Each coordinate should be a sequence (list or tuple)"
                    )

                if ndim is None:
                    ndim = len(coord)
                    self._checkdim(ndim)
                elif len(coord) != ndim:
                    raise TypeError("Dimension mismatch.")

        # Creating a coordinate sequence object because it is easier to
        # set the points using its methods.
        cs = GEOSCoordSeq(capi.create_cs(ncoords, ndim), z=bool(ndim == 3))
        point_setter = cs._set_point_3d if ndim == 3 else cs._set_point_2d

        for i in range(ncoords):
            if numpy_coords:
                point_coords = coords[i, :]
            elif isinstance(coords[i], Point):
                point_coords = coords[i].tuple
            else:
                point_coords = coords[i]
            point_setter(i, point_coords)

        # Calling the base geometry initialization with the returned pointer
        #  from the function.
        super().__init__(self._init_func(cs.ptr), srid=srid)