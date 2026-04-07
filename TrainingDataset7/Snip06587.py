def get_distance(self, f, value, lookup_type):
        value = value[0]
        if isinstance(value, Distance):
            if f.geodetic(self.connection):
                raise ValueError(
                    "Only numeric values of degree units are allowed on "
                    "geodetic distance queries."
                )
            dist_param = getattr(
                value, Distance.unit_attname(f.units_name(self.connection))
            )
        else:
            dist_param = value
        return [dist_param]