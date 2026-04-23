def __init__(self, srs_input="", srs_type="user", axis_order=None):
        """
        Create a GDAL OSR Spatial Reference object from the given input.
        The input may be string of OGC Well Known Text (WKT), an integer
        EPSG code, a PROJ string, and/or a projection "well known" shorthand
        string (one of 'WGS84', 'WGS72', 'NAD27', 'NAD83').
        """
        if not isinstance(axis_order, (NoneType, AxisOrder)):
            raise ValueError(
                "SpatialReference.axis_order must be an AxisOrder instance."
            )
        self.axis_order = axis_order or AxisOrder.TRADITIONAL
        if srs_type == "wkt":
            self.ptr = capi.new_srs(c_char_p(b""))
            self.import_wkt(srs_input)
            if self.axis_order == AxisOrder.TRADITIONAL:
                capi.set_axis_strategy(self.ptr, self.axis_order)
            return
        elif isinstance(srs_input, str):
            try:
                # If SRID is a string, e.g., '4326', then make acceptable
                # as user input.
                srid = int(srs_input)
                srs_input = "EPSG:%d" % srid
            except ValueError:
                pass
        elif isinstance(srs_input, int):
            # EPSG integer code was input.
            srs_type = "epsg"
        elif isinstance(srs_input, self.ptr_type):
            srs = srs_input
            srs_type = "ogr"
        else:
            raise TypeError('Invalid SRS type "%s"' % srs_type)

        if srs_type == "ogr":
            # Input is already an SRS pointer.
            srs = srs_input
        else:
            # Creating a new SRS pointer, using the string buffer.
            buf = c_char_p(b"")
            srs = capi.new_srs(buf)

        # If the pointer is NULL, throw an exception.
        if not srs:
            raise SRSException(
                "Could not create spatial reference from: %s" % srs_input
            )
        else:
            self.ptr = srs

        if self.axis_order == AxisOrder.TRADITIONAL:
            capi.set_axis_strategy(self.ptr, self.axis_order)
        # Importing from either the user input string or an integer SRID.
        if srs_type == "user":
            self.import_user_input(srs_input)
        elif srs_type == "epsg":
            self.import_epsg(srs_input)