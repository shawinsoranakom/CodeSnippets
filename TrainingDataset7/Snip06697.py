def to_pgraster(rast):
    """
    Convert a GDALRaster into PostGIS Raster format.
    """
    # Prepare the raster header data as a tuple. The first two numbers are
    # the endianness and the PostGIS Raster Version, both are fixed by
    # PostGIS at the moment.
    rasterheader = (
        1,
        0,
        len(rast.bands),
        rast.scale.x,
        rast.scale.y,
        rast.origin.x,
        rast.origin.y,
        rast.skew.x,
        rast.skew.y,
        rast.srs.srid,
        rast.width,
        rast.height,
    )

    # Pack raster header.
    result = pack(POSTGIS_HEADER_STRUCTURE, rasterheader)

    for band in rast.bands:
        # The PostGIS raster band header has exactly two elements, a 8BUI byte
        # and the nodata value.
        #
        # The 8BUI stores both the PostGIS pixel data type and a nodata flag.
        # It is composed as the datatype with BANDTYPE_FLAG_HASNODATA (1 << 6)
        # for existing nodata values:
        #   8BUI_VALUE = PG_PIXEL_TYPE (0-11) | BANDTYPE_FLAG_HASNODATA
        #
        # For example, if the byte value is 71, then the datatype is
        #   71 & ~BANDTYPE_FLAG_HASNODATA = 7 (32BSI)
        # and the nodata value is True.
        structure = "B" + GDAL_TO_STRUCT[band.datatype()]

        # Get band pixel type in PostGIS notation
        pixeltype = GDAL_TO_POSTGIS[band.datatype()]

        # Set the nodata flag
        if band.nodata_value is not None:
            pixeltype |= BANDTYPE_FLAG_HASNODATA

        # Pack band header
        bandheader = pack(structure, (pixeltype, band.nodata_value or 0))

        # Add packed header and band data to result
        result += bandheader + band.data(as_memoryview=True)

    return result