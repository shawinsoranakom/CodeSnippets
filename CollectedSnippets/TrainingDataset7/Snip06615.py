def get_distance(self, f, value, lookup_type):
        """
        Return the distance parameters given the value and the lookup type.
        On Oracle, geometry columns with a geodetic coordinate system behave
        implicitly like a geography column, and thus meters will be used as
        the distance parameter on them.
        """
        if not value:
            return []
        value = value[0]
        if isinstance(value, Distance):
            if f.geodetic(self.connection):
                dist_param = value.m
            else:
                dist_param = getattr(
                    value, Distance.unit_attname(f.units_name(self.connection))
                )
        else:
            dist_param = value

        # dwithin lookups on Oracle require a special string parameter
        # that starts with "distance=".
        if lookup_type == "dwithin":
            dist_param = "distance=%s" % dist_param

        return [dist_param]