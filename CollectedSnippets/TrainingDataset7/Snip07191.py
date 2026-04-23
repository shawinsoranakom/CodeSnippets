def country_code(self, query):
        "Return the country code for the given IP Address or FQDN."
        return self.country(query)["country_code"]