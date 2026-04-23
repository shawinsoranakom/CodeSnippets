def mock_api_call(cmd: str, fetch_data: bool = False) -> dict[str, Any]:
    """Mock AEMET OpenData API calls."""
    if cmd == "maestro/municipio/id28065":
        return TOWN_DATA_MOCK
    if cmd == "maestro/municipios":
        return TOWNS_DATA_MOCK
    if (
        cmd
        == "observacion/convencional/datos/estacion/3195"  # codespell:ignore convencional
    ):
        return STATION_DATA_MOCK
    if cmd == "observacion/convencional/todas":  # codespell:ignore convencional
        return STATIONS_DATA_MOCK
    if cmd == "prediccion/especifica/municipio/diaria/28065":
        return FORECAST_DAILY_DATA_MOCK
    if cmd == "prediccion/especifica/municipio/horaria/28065":
        return FORECAST_HOURLY_DATA_MOCK
    if cmd == "red/radar/nacional":
        return RADAR_DATA_MOCK

    return {}