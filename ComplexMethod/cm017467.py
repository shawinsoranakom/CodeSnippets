def __init__(self, path=None, cache=0, country=None, city=None):
        """
        Initialize the GeoIP object. No parameters are required to use default
        settings. Keyword arguments may be passed in to customize the locations
        of the GeoIP datasets.

        * path: Base directory to where GeoIP data is located or the full path
            to where the city or country data files (*.mmdb) are located.
            Assumes that both the city and country data sets are located in
            this directory; overrides the GEOIP_PATH setting.

        * cache: The cache settings when opening up the GeoIP datasets. May be
            an integer in (0, 1, 2, 4, 8) corresponding to the MODE_AUTO,
            MODE_MMAP_EXT, MODE_MMAP, MODE_FILE, and MODE_MEMORY,
            `GeoIPOptions` C API settings, respectively. Defaults to 0,
            meaning MODE_AUTO.

        * country: The name of the GeoIP country data file. Defaults to
            'GeoLite2-Country.mmdb'; overrides the GEOIP_COUNTRY setting.

        * city: The name of the GeoIP city data file. Defaults to
            'GeoLite2-City.mmdb'; overrides the GEOIP_CITY setting.
        """
        if cache not in self.cache_options:
            raise GeoIP2Exception("Invalid GeoIP caching option: %s" % cache)

        path = path or getattr(settings, "GEOIP_PATH", None)
        city = city or getattr(settings, "GEOIP_CITY", "GeoLite2-City.mmdb")
        country = country or getattr(settings, "GEOIP_COUNTRY", "GeoLite2-Country.mmdb")

        if not path:
            raise GeoIP2Exception(
                "GeoIP path must be provided via parameter or the GEOIP_PATH setting."
            )

        path = to_path(path)

        # Try the path first in case it is the full path to a database.
        for path in (path, path / city, path / country):
            if path.is_file():
                self._path = path
                self._reader = geoip2.database.Reader(path, mode=cache)
                break
        else:
            raise GeoIP2Exception(
                "Path must be a valid database or directory containing databases."
            )

        database_type = self._metadata.database_type
        if database_type not in SUPPORTED_DATABASE_TYPES:
            raise GeoIP2Exception(f"Unable to handle database edition: {database_type}")