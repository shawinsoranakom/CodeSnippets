def from_pgraster(data):
    """
    Convert a PostGIS HEX String into a dictionary.
    """
    if data is None:
        return

    # Split raster header from data
    header, data = chunk(data, 122)
    header = unpack(POSTGIS_HEADER_STRUCTURE, header)

    # Parse band data
    bands = []
    pixeltypes = []
    while data:
        # Get pixel type for this band
        pixeltype_with_flags, data = chunk(data, 2)
        pixeltype_with_flags = unpack("B", pixeltype_with_flags)[0]
        pixeltype = pixeltype_with_flags & BANDTYPE_PIXTYPE_MASK

        # Convert datatype from PostGIS to GDAL & get pack type and size
        pixeltype = POSTGIS_TO_GDAL[pixeltype]
        pack_type = GDAL_TO_STRUCT[pixeltype]
        pack_size = 2 * STRUCT_SIZE[pack_type]

        # Parse band nodata value. The nodata value is part of the
        # PGRaster string even if the nodata flag is True, so it always
        # has to be chunked off the data string.
        nodata, data = chunk(data, pack_size)
        nodata = unpack(pack_type, nodata)[0]

        # Chunk and unpack band data (pack size times nr of pixels)
        band, data = chunk(data, pack_size * header[10] * header[11])
        band_result = {"data": bytes.fromhex(band)}

        # Set the nodata value if the nodata flag is set.
        if pixeltype_with_flags & BANDTYPE_FLAG_HASNODATA:
            band_result["nodata_value"] = nodata

        # Append band data to band list
        bands.append(band_result)

        # Store pixeltype of this band in pixeltypes array
        pixeltypes.append(pixeltype)

    # Check that all bands have the same pixeltype.
    # This is required by GDAL. PostGIS rasters could have different pixeltypes
    # for bands of the same raster.
    if len(set(pixeltypes)) != 1:
        raise ValidationError("Band pixeltypes are not all equal.")

    return {
        "srid": int(header[9]),
        "width": header[10],
        "height": header[11],
        "datatype": pixeltypes[0],
        "origin": (header[5], header[6]),
        "scale": (header[3], header[4]),
        "skew": (header[7], header[8]),
        "bands": bands,
    }