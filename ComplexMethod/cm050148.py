def _get_localisation(self, latitude, longitude):
        # try to get city and/or country from request.geoip first
        # if not possible, get them from latitude and longitude
        city = request.geoip.city.name
        country_code = request.geoip.country_code
        postcode = False
        if not (city and country_code):
            # for now, we use openstreetmap, if needed, we will add a setting like "partner geolocation" that let the
            # user decide wich provider to use to localise the partner.
            result = self._call_openstreetmap_reverse(latitude, longitude)
            if result and (address := result.get("address")):
                country_code = address.get("country_code")
                city = address.get("city_district") or address.get("town") or address.get("village") or address.get("city")
                postcode = address.get("postcode")

        country = self.env["res.country"].search([("code", "=", country_code.upper())], limit=1) if country_code else False

        res = postcode or ""
        if city:
            res += f" {city}" if res else city
        if country:
            res += f", {country.name}" if res else country.name

        return res or _("Unknown")