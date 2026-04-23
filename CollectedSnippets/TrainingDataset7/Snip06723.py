def get_distance(self, f, value, lookup_type):
        """
        Return the distance parameters for the given geometry field,
        lookup value, and lookup type.
        """
        if not value:
            return []
        value = value[0]
        if isinstance(value, Distance):
            if f.geodetic(self.connection):
                if lookup_type == "dwithin":
                    raise ValueError(
                        "Only numeric values of degree units are allowed on "
                        "geographic DWithin queries."
                    )
                dist_param = value.m
            else:
                dist_param = getattr(
                    value, Distance.unit_attname(f.units_name(self.connection))
                )
        else:
            dist_param = value
        return [dist_param]