def from_db_value(self, value, expression, connection):
        if value is None:
            return
        # If the database returns a Decimal, convert it to a float as expected
        # by the Python geometric objects.
        if isinstance(value, Decimal):
            value = float(value)
        # If the units are known, convert value into area measure.
        area_att = connection.ops.get_area_att_for_field(self.geo_field)
        return Area(**{area_att: value}) if area_att else value