def geodetic(self, connection):
        """
        Return true if this field's SRID corresponds with a coordinate
        system that uses non-projected units (e.g., latitude/longitude).
        """
        return get_srid_info(self.srid, connection).geodetic