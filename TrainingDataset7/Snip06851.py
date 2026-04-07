def from_db_value(self, value, expression, connection):
        if value is None:
            return
        distance_att = connection.ops.get_distance_att_for_field(self.geo_field)
        return Distance(**{distance_att: value}) if distance_att else value