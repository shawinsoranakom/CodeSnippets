def _get_wind_direction(wind_direction_degree: float) -> str:
    """Convert wind direction degree to named direction."""
    if 11.25 <= wind_direction_degree < 33.75:
        return "NNE"
    if 33.75 <= wind_direction_degree < 56.25:
        return "NE"
    if 56.25 <= wind_direction_degree < 78.75:
        return "ENE"
    if 78.75 <= wind_direction_degree < 101.25:
        return "E"
    if 101.25 <= wind_direction_degree < 123.75:
        return "ESE"
    if 123.75 <= wind_direction_degree < 146.25:
        return "SE"
    if 146.25 <= wind_direction_degree < 168.75:
        return "SSE"
    if 168.75 <= wind_direction_degree < 191.25:
        return "S"
    if 191.25 <= wind_direction_degree < 213.75:
        return "SSW"
    if 213.75 <= wind_direction_degree < 236.25:
        return "SW"
    if 236.25 <= wind_direction_degree < 258.75:
        return "WSW"
    if 258.75 <= wind_direction_degree < 281.25:
        return "W"
    if 281.25 <= wind_direction_degree < 303.75:
        return "WNW"
    if 303.75 <= wind_direction_degree < 326.25:
        return "NW"
    if 326.25 <= wind_direction_degree < 348.75:
        return "NNW"
    return "N"