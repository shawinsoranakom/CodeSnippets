def city(self, query):
        """
        Return a dictionary of city information for the given IP address or
        Fully Qualified Domain Name (FQDN). Some information in the dictionary
        may be undefined (None).
        """
        response = self._query(query, require_city=True)
        region = response.subdivisions[0] if response.subdivisions else None
        return {
            "accuracy_radius": response.location.accuracy_radius,
            "city": response.city.name,
            "continent_code": response.continent.code,
            "continent_name": response.continent.name,
            "country_code": response.country.iso_code,
            "country_name": response.country.name,
            "is_in_european_union": response.country.is_in_european_union,
            "latitude": response.location.latitude,
            "longitude": response.location.longitude,
            "metro_code": response.location.metro_code,
            "postal_code": response.postal.code,
            "region_code": region.iso_code if region else None,
            "region_name": region.name if region else None,
            "time_zone": response.location.time_zone,
            # Kept for backward compatibility.
            "dma_code": response.location.metro_code,
            "region": region.iso_code if region else None,
        }