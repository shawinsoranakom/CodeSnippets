def _initialize_geo_bypass(self, geo_bypass_context):
        """
        Initialize geo restriction bypass mechanism.

        This method is used to initialize geo bypass mechanism based on faking
        X-Forwarded-For HTTP header. A random country from provided country list
        is selected and a random IP belonging to this country is generated. This
        IP will be passed as X-Forwarded-For HTTP header in all subsequent
        HTTP requests.

        This method will be used for initial geo bypass mechanism initialization
        during the instance initialization with _GEO_COUNTRIES and
        _GEO_IP_BLOCKS.

        You may also manually call it from extractor's code if geo bypass
        information is not available beforehand (e.g. obtained during
        extraction) or due to some other reason. In this case you should pass
        this information in geo bypass context passed as first argument. It may
        contain following fields:

        countries:  List of geo unrestricted countries (similar
                    to _GEO_COUNTRIES)
        ip_blocks:  List of geo unrestricted IP blocks in CIDR notation
                    (similar to _GEO_IP_BLOCKS)

        """
        if not self._x_forwarded_for_ip:

            # Geo bypass mechanism is explicitly disabled by user
            if not self.get_param('geo_bypass', True):
                return

            if not geo_bypass_context:
                geo_bypass_context = {}

            # Backward compatibility: previously _initialize_geo_bypass
            # expected a list of countries, some 3rd party code may still use
            # it this way
            if isinstance(geo_bypass_context, (list, tuple)):
                geo_bypass_context = {
                    'countries': geo_bypass_context,
                }

            # The whole point of geo bypass mechanism is to fake IP
            # as X-Forwarded-For HTTP header based on some IP block or
            # country code.

            # Path 1: bypassing based on IP block in CIDR notation

            # Explicit IP block specified by user, use it right away
            # regardless of whether extractor is geo bypassable or not
            ip_block = self.get_param('geo_bypass_ip_block', None)

            # Otherwise use random IP block from geo bypass context but only
            # if extractor is known as geo bypassable
            if not ip_block:
                ip_blocks = geo_bypass_context.get('ip_blocks')
                if self._GEO_BYPASS and ip_blocks:
                    ip_block = random.choice(ip_blocks)

            if ip_block:
                self._x_forwarded_for_ip = GeoUtils.random_ipv4(ip_block)
                self.write_debug(f'Using fake IP {self._x_forwarded_for_ip} as X-Forwarded-For')
                return

            # Path 2: bypassing based on country code

            # Explicit country code specified by user, use it right away
            # regardless of whether extractor is geo bypassable or not
            country = self.get_param('geo_bypass_country', None)

            # Otherwise use random country code from geo bypass context but
            # only if extractor is known as geo bypassable
            if not country:
                countries = geo_bypass_context.get('countries')
                if self._GEO_BYPASS and countries:
                    country = random.choice(countries)

            if country:
                self._x_forwarded_for_ip = GeoUtils.random_ipv4(country)
                self._downloader.write_debug(
                    f'Using fake IP {self._x_forwarded_for_ip} ({country.upper()}) as X-Forwarded-For')