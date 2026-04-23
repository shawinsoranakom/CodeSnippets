def spheroid(self, connection):
        return get_srid_info(self.srid, connection).spheroid