def gdal_version():
    "Return only the GDAL version number information."
    return _version_info(b"RELEASE_NAME")