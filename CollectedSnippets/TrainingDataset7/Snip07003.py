def _geos_ptr(self):
        from django.contrib.gis import geos

        return geos.Point._create_empty() if self.empty else super()._geos_ptr()