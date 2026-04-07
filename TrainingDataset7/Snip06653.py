def __init_subclass__(cls, base_dumper):
                super().__init_subclass__()

                cls.GeometryDumper = type(
                    "GeometryDumper", (base_dumper,), {"oid": geo_oid}
                )
                cls.GeographyDumper = type(
                    "GeographyDumper", (base_dumper,), {"oid": geog_oid}
                )
                cls.RasterDumper = type(
                    "RasterDumper", (BaseTextDumper,), {"oid": raster_oid}
                )