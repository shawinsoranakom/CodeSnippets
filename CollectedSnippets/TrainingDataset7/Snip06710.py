def supports_area_geodetic(self):
        return bool(self.connection.ops.geom_lib_version())