def gdal_version_info():
    ver = gdal_version()
    m = re.match(rb"^(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<subminor>\d+))?", ver)
    if not m:
        raise GDALException('Could not parse GDAL version string "%s"' % ver)
    major, minor, subminor = m.groups()
    return (int(major), int(minor), subminor and int(subminor))