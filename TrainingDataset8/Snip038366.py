def _fix_pydeck_mapbox_api_warning() -> None:
    """Sets MAPBOX_API_KEY environment variable needed for PyDeck otherwise it will throw an exception"""

    os.environ["MAPBOX_API_KEY"] = config.get_option("mapbox.token")