def __init__(self, *args, **kwargs):
        """
        Initialize on an exterior ring and a sequence of holes (both
        instances may be either LinearRing instances, or a tuple/list
        that may be constructed into a LinearRing).

        Examples of initialization, where shell, hole1, and hole2 are
        valid LinearRing geometries:
        >>> from django.contrib.gis.geos import LinearRing, Polygon
        >>> shell = hole1 = hole2 = LinearRing()
        >>> poly = Polygon(shell, hole1, hole2)
        >>> poly = Polygon(shell, (hole1, hole2))

        >>> # Example where a tuple parameters are used:
        >>> poly = Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0)),
        ...                ((4, 4), (4, 6), (6, 6), (6, 4), (4, 4)))
        """
        if not args:
            super().__init__(self._create_polygon(0, None), **kwargs)
            return

        # Getting the ext_ring and init_holes parameters from the argument list
        ext_ring, *init_holes = args
        n_holes = len(init_holes)

        # If initialized as Polygon(shell, (LinearRing, LinearRing))
        # [for backward-compatibility]
        if n_holes == 1 and isinstance(init_holes[0], (tuple, list)):
            if not init_holes[0]:
                init_holes = ()
                n_holes = 0
            elif isinstance(init_holes[0][0], LinearRing):
                init_holes = init_holes[0]
                n_holes = len(init_holes)

        polygon = self._create_polygon(n_holes + 1, [ext_ring, *init_holes])
        super().__init__(polygon, **kwargs)