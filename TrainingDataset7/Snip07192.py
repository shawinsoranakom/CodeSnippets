def country_name(self, query):
        "Return the country name for the given IP Address or FQDN."
        return self.country(query)["country_name"]