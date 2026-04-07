def units_name(self, connection):
        return get_srid_info(self.srid, connection).units_name