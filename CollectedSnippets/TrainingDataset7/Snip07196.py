def geos(self, query):
        "Return a GEOS Point object for the given query."
        # Allows importing and using GeoIP2() when GEOS is not installed.
        from django.contrib.gis.geos import Point

        return Point(self.lon_lat(query), srid=4326)