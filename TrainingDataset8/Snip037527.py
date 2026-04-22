def to_deckgl_json(data: Data, zoom: Optional[int]) -> str:
    if data is None:
        return json.dumps(_DEFAULT_MAP)

    # TODO(harahu): iterables don't have the empty attribute. This is either
    # a bug, or the documented data type is too broad. One or the other
    # should be addressed
    if hasattr(data, "empty") and data.empty:
        return json.dumps(_DEFAULT_MAP)

    data = type_util.convert_anything_to_df(data)

    if "lat" in data:
        lat = "lat"
    elif "latitude" in data:
        lat = "latitude"
    else:
        raise StreamlitAPIException(
            'Map data must contain a column named "latitude" or "lat".'
        )

    if "lon" in data:
        lon = "lon"
    elif "longitude" in data:
        lon = "longitude"
    else:
        raise StreamlitAPIException(
            'Map data must contain a column called "longitude" or "lon".'
        )

    if data[lon].isnull().values.any() or data[lat].isnull().values.any():
        raise StreamlitAPIException("Latitude and longitude data must be numeric.")

    min_lat = data[lat].min()
    max_lat = data[lat].max()
    min_lon = data[lon].min()
    max_lon = data[lon].max()
    center_lat = (max_lat + min_lat) / 2.0
    center_lon = (max_lon + min_lon) / 2.0
    range_lon = abs(max_lon - min_lon)
    range_lat = abs(max_lat - min_lat)

    if zoom is None:
        if range_lon > range_lat:
            longitude_distance = range_lon
        else:
            longitude_distance = range_lat
        zoom = _get_zoom_level(longitude_distance)

    # "+1" because itertuples includes the row index.
    lon_col_index = data.columns.get_loc(lon) + 1
    lat_col_index = data.columns.get_loc(lat) + 1
    final_data = []
    for row in data.itertuples():
        final_data.append(
            {"lon": float(row[lon_col_index]), "lat": float(row[lat_col_index])}
        )

    default = copy.deepcopy(_DEFAULT_MAP)
    default["initialViewState"]["latitude"] = center_lat
    default["initialViewState"]["longitude"] = center_lon
    default["initialViewState"]["zoom"] = zoom
    default["layers"] = [
        {
            "@@type": "ScatterplotLayer",
            "getPosition": "@@=[lon, lat]",
            "getRadius": 10,
            "radiusScale": 10,
            "radiusMinPixels": 3,
            "getFillColor": _DEFAULT_COLOR,
            "data": final_data,
        }
    ]
    return json.dumps(default)