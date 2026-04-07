def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return
        area_att = connection.ops.get_area_att_for_field(self.geo_field)
        return getattr(value, area_att) if area_att else value