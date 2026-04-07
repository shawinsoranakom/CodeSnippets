def register_geometry_adapters(self, pg_connection, clear_caches=False):
            if clear_caches:
                for typename in self._type_infos:
                    self._type_infos[typename].pop(self.alias, None)

            geo_oid = self._register_type(pg_connection, "geometry")
            geog_oid = self._register_type(pg_connection, "geography")
            raster_oid = self._register_type(pg_connection, "raster")

            PostGISTextDumper, PostGISBinaryDumper = postgis_adapters(
                geo_oid, geog_oid, raster_oid
            )
            pg_connection.adapters.register_dumper(PostGISAdapter, PostGISTextDumper)
            pg_connection.adapters.register_dumper(PostGISAdapter, PostGISBinaryDumper)