def _check_connection(self, connection):
        # Make sure raster fields are used only on backends with raster
        # support.
        if (
            not connection.features.gis_enabled
            or not connection.features.supports_raster
        ):
            raise ImproperlyConfigured(
                "Raster fields require backends with raster support."
            )