def geos(self):
        "Return a GEOSGeometry object from this OGRGeometry."
        if self.geos_support:
            from django.contrib.gis.geos import GEOSGeometry

            return GEOSGeometry(self._geos_ptr(), self.srid)
        else:
            from django.contrib.gis.geos import GEOSException

            raise GEOSException(f"GEOS does not support {self.__class__.__qualname__}.")