def __init__(self, geo_input, srid=None):
        """
        The base constructor for GEOS geometry objects. It may take the
        following inputs:

         * strings:
            - WKT
            - HEXEWKB (a PostGIS-specific canonical form)
            - GeoJSON (requires GDAL)
         * memoryview:
            - WKB

        The `srid` keyword specifies the Source Reference Identifier (SRID)
        number for this Geometry. If not provided, it defaults to None.
        """
        input_srid = None
        if isinstance(geo_input, bytes):
            geo_input = force_str(geo_input)
        if isinstance(geo_input, str):
            wkt_m = wkt_regex.match(geo_input)
            if wkt_m:
                # Handle WKT input.
                if wkt_m["srid"]:
                    input_srid = int(wkt_m["srid"])
                g = self._from_wkt(force_bytes(wkt_m["wkt"]))
            elif hex_regex.match(geo_input):
                # Handle HEXEWKB input.
                g = wkb_r().read(force_bytes(geo_input))
            elif json_regex.match(geo_input):
                # Handle GeoJSON input.
                ogr = gdal.OGRGeometry.from_json(geo_input)
                g = ogr._geos_ptr()
                input_srid = ogr.srid
            else:
                raise ValueError("String input unrecognized as WKT EWKT, and HEXEWKB.")
        elif isinstance(geo_input, GEOM_PTR):
            # When the input is a pointer to a geometry (GEOM_PTR).
            g = geo_input
        elif isinstance(geo_input, memoryview):
            # When the input is a memoryview (WKB).
            g = wkb_r().read(geo_input)
        elif isinstance(geo_input, GEOSGeometry):
            g = capi.geom_clone(geo_input.ptr)
        else:
            raise TypeError("Improper geometry input type: %s" % type(geo_input))

        if not g:
            raise GEOSException("Could not initialize GEOS Geometry with given input.")

        input_srid = input_srid or capi.geos_get_srid(g) or None
        if input_srid and srid and input_srid != srid:
            raise ValueError("Input geometry already has SRID: %d." % input_srid)

        super().__init__(g, None)
        # Set the SRID, if given.
        srid = input_srid or srid
        if srid and isinstance(srid, int):
            self.srid = srid