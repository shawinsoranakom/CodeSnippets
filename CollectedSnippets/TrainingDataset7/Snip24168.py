def item_geometry(self, item):
        from django.contrib.gis.geos import Polygon

        return Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))