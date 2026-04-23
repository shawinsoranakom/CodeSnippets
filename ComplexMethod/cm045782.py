def geolocate_external(location: str, forbidden_list=[], cache=None):
    for forbidden in forbidden_list:
        if re.search(forbidden, location, re.IGNORECASE):
            return GeolocatorInvalidFlags.FORBIDDEN.value

    geolocated = (
        cache[location]
        if cache is not None and location in cache
        else geolocate_coarse_pelias(location)
    )
    if geolocated == GeolocatorInvalidFlags.NORESULT.value:
        return geolocated
    if "area" in geolocated["geom"] and geolocated["geom"]["area"] > AREA_THRESHOLD:
        return GeolocatorInvalidFlags.TOO_LARGE_AREA.value
    return (geolocated["geom"]["lon"], geolocated["geom"]["lat"])