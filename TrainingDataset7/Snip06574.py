def get_distance_att_for_field(self, field):
        dist_att = None
        if field.geodetic(self.connection):
            if self.connection.features.supports_distance_geodetic:
                dist_att = "m"
        else:
            units = field.units_name(self.connection)
            if units:
                dist_att = DistanceMeasure.unit_attname(units)
        return dist_att