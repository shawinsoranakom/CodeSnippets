def __getitem__(self, item):
        if item == 'country_name':
            return self.country_name

        if item == 'country_code':
            return self.country_code

        if item == 'city':
            return self.city.name

        if item == 'latitude':
            return self.location.latitude

        if item == 'longitude':
            return self.location.longitude

        if item == 'region':
            return self.subdivisions[0].iso_code if self.subdivisions else None

        if item == 'time_zone':
            return self.location.time_zone

        raise KeyError(item)