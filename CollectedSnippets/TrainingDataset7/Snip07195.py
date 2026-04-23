def lat_lon(self, query):
        "Return a tuple of the (latitude, longitude) for the given query."
        data = self.city(query)
        return data["latitude"], data["longitude"]