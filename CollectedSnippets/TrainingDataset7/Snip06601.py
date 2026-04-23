def _fix_geometry_collection(cls, coll):
        """
        Fix polygon orientations in geometry collections as described in
        __init__().
        """
        coll = coll.clone()
        for i, geom in enumerate(coll):
            if isinstance(geom, Polygon):
                coll[i] = cls._fix_polygon(geom, clone=False)
        return coll