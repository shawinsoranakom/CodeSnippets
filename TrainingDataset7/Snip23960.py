def get_names(self, qs):
        cities = [c.name for c in qs]
        cities.sort()
        return cities