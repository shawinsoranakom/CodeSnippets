def get_geoms(self, geos=False):
        """
        Return a list containing the OGRGeometry for every Feature in
        the Layer.
        """
        if geos:
            from django.contrib.gis.geos import GEOSGeometry

            return [GEOSGeometry(feat.geom.wkb) for feat in self]
        else:
            return [feat.geom for feat in self]