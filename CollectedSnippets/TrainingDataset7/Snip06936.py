def __init__(self, geom_input, srs=None):
        """Initialize Geometry on either WKT or an OGR pointer as input."""
        str_instance = isinstance(geom_input, str)

        # If HEX, unpack input to a binary buffer.
        if str_instance and hex_regex.match(geom_input):
            geom_input = memoryview(bytes.fromhex(geom_input))
            str_instance = False

        # Constructing the geometry,
        if str_instance:
            wkt_m = wkt_regex.match(geom_input)
            json_m = json_regex.match(geom_input)
            if wkt_m:
                if wkt_m["srid"]:
                    # If there's EWKT, set the SRS w/value of the SRID.
                    srs = int(wkt_m["srid"])
                if wkt_m["type"].upper() == "LINEARRING":
                    # OGR_G_CreateFromWkt doesn't work with LINEARRING WKT.
                    #  See https://trac.osgeo.org/gdal/ticket/1992.
                    g = capi.create_geom(OGRGeomType(wkt_m["type"]).num)
                    capi.import_wkt(g, byref(c_char_p(wkt_m["wkt"].encode())))
                else:
                    g = capi.from_wkt(
                        byref(c_char_p(wkt_m["wkt"].encode())), None, byref(c_void_p())
                    )
            elif json_m:
                g = self._from_json(geom_input.encode())
            else:
                # Seeing if the input is a valid short-hand string
                # (e.g., 'Point', 'POLYGON').
                OGRGeomType(geom_input)
                g = capi.create_geom(OGRGeomType(geom_input).num)
        elif isinstance(geom_input, memoryview):
            # WKB was passed in
            g = self._from_wkb(geom_input)
        elif isinstance(geom_input, OGRGeomType):
            # OGRGeomType was passed in, an empty geometry will be created.
            g = capi.create_geom(geom_input.num)
        elif isinstance(geom_input, self.ptr_type):
            # OGR pointer (c_void_p) was the input.
            g = geom_input
        else:
            raise GDALException(
                "Invalid input type for OGR Geometry construction: %s"
                % type(geom_input)
            )

        # Now checking the Geometry pointer before finishing initialization
        # by setting the pointer for the object.
        if not g:
            raise GDALException(
                "Cannot create OGR Geometry from input: %s" % geom_input
            )
        self.ptr = g

        # Assigning the SpatialReference object to the geometry, if valid.
        if srs:
            self.srs = srs

        # Setting the class depending upon the OGR Geometry Type
        if (geo_class := GEO_CLASSES.get(self.geom_type.num)) is None:
            raise TypeError(f"Unsupported geometry type: {self.geom_type}")
        self.__class__ = geo_class