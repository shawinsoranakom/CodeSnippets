def get_area_att_for_field(self, field):
        if field.geodetic(self.connection):
            if self.connection.features.supports_area_geodetic:
                return "sq_m"
            raise NotImplementedError(
                "Area on geodetic coordinate systems not supported."
            )
        else:
            units_name = field.units_name(self.connection)
            if units_name:
                return AreaMeasure.unit_attname(units_name)