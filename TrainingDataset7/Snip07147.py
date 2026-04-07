def __getitem__(self, target):
        """
        Return the value of the given string attribute node, None if the node
        doesn't exist. Can also take a tuple as a parameter, (target, child),
        where child is the index of the attribute in the WKT. For example:

        >>> wkt = (
        ...     'GEOGCS["WGS 84",'
        ...     '  DATUM["WGS_1984, ... AUTHORITY["EPSG","4326"]'
        ...     ']'
        ... )
        >>> srs = SpatialReference(wkt) # could also use 'WGS84', or 4326
        >>> print(srs['GEOGCS'])
        WGS 84
        >>> print(srs['DATUM'])
        WGS_1984
        >>> print(srs['AUTHORITY'])
        EPSG
        >>> print(srs['AUTHORITY', 1]) # The authority value
        4326
        >>> print(srs['TOWGS84', 4]) # the fourth value in this wkt
        0
        >>> # For the units authority, have to use the pipe symbole.
        >>> print(srs['UNIT|AUTHORITY'])
        EPSG
        >>> print(srs['UNIT|AUTHORITY', 1]) # The authority value for the units
        9122
        """
        if isinstance(target, tuple):
            return self.attr_value(*target)
        else:
            return self.attr_value(target)