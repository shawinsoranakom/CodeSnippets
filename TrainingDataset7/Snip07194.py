def lon_lat(self, query):
        "Return a tuple of the (longitude, latitude) for the given query."
        data = self.city(query)
        return data["longitude"], data["latitude"]