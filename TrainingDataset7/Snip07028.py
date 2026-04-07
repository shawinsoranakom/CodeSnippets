def __init__(self, type_input):
        "Figure out the correct OGR Type based upon the input."
        if isinstance(type_input, OGRGeomType):
            num = type_input.num
        elif isinstance(type_input, str):
            type_input = type_input.lower()
            if type_input == "geometry":
                type_input = "unknown"
            num = self._str_types.get(type_input)
            if num is None:
                raise GDALException('Invalid OGR String Type "%s"' % type_input)
        elif isinstance(type_input, int):
            if type_input not in self._types:
                raise GDALException("Invalid OGR Integer Type: %d" % type_input)
            num = type_input
        else:
            raise TypeError("Invalid OGR input type given.")

        # Setting the OGR geometry type number.
        self.num = num