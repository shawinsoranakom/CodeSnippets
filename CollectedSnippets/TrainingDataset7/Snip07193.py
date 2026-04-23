def country(self, query):
        """
        Return a dictionary with the country code and name when given an
        IP address or a Fully Qualified Domain Name (FQDN). For example, both
        '24.124.1.80' and 'djangoproject.com' are valid parameters.
        """
        response = self._query(query, require_city=False)
        return {
            "continent_code": response.continent.code,
            "continent_name": response.continent.name,
            "country_code": response.country.iso_code,
            "country_name": response.country.name,
            "is_in_european_union": response.country.is_in_european_union,
        }