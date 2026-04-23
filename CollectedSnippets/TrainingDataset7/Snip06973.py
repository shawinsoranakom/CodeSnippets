def _geos_ptr(self):
        from django.contrib.gis.geos import GEOSGeometry

        return GEOSGeometry._from_wkb(self.wkb)