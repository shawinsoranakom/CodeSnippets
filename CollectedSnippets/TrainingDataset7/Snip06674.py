def get_distance(self, f, dist_val, lookup_type):
        """
        Retrieve the distance parameters for the given geometry field,
        distance lookup value, and the distance lookup type.

        This is the most complex implementation of the spatial backends due to
        what is supported on geodetic geometry columns vs. what's available on
        projected geometry columns. In addition, it has to take into account
        the geography column type.
        """
        # Getting the distance parameter
        value = dist_val[0]

        # Shorthand boolean flags.
        geodetic = f.geodetic(self.connection)
        geography = f.geography

        if isinstance(value, Distance):
            if geography:
                dist_param = value.m
            elif geodetic:
                if lookup_type == "dwithin":
                    raise ValueError(
                        "Only numeric values of degree units are "
                        "allowed on geographic DWithin queries."
                    )
                dist_param = value.m
            else:
                dist_param = getattr(
                    value, Distance.unit_attname(f.units_name(self.connection))
                )
        else:
            # Assuming the distance is in the units of the field.
            dist_param = value

        return [dist_param]