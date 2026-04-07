def units(self, connection):
        return get_srid_info(self.srid, connection).units