def __init__(self, x=None, y=None, z=None, srid=None):
        """
        The Point object may be initialized with either a tuple, or individual
        parameters.

        For example:
        >>> p = Point((5, 23))  # 2D point, passed in as a tuple
        >>> p = Point(5, 23, 8)  # 3D point, passed as individual parameters
        """
        if x is None:
            coords = []
        elif isinstance(x, (tuple, list)):
            # Here a tuple or list was passed in under the `x` parameter.
            coords = x
        elif isinstance(x, (float, int)) and isinstance(y, (float, int)):
            # Here X, Y, and (optionally) Z were passed in individually, as
            # parameters.
            if isinstance(z, (float, int)):
                coords = [x, y, z]
            else:
                coords = [x, y]
        else:
            raise TypeError("Invalid parameters given for Point initialization.")

        point = self._create_point(len(coords), coords)

        # Initializing using the address returned from the GEOS
        #  createPoint factory.
        super().__init__(point, srid=srid)