def _query(self, query, *, require_city=False):
        if not isinstance(query, (str, ipaddress.IPv4Address, ipaddress.IPv6Address)):
            raise TypeError(
                "GeoIP query must be a string or instance of IPv4Address or "
                "IPv6Address, not type %s" % type(query).__name__,
            )

        if require_city and not self.is_city:
            raise GeoIP2Exception(f"Invalid GeoIP city data file: {self._path}")

        if isinstance(query, str):
            try:
                validate_ipv46_address(query)
            except ValidationError:
                # GeoIP2 only takes IP addresses, so try to resolve a hostname.
                query = socket.gethostbyname(query)

        function = self._reader.city if self.is_city else self._reader.country
        return function(query)