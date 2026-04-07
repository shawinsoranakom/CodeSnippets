def __init__(self, ptr, cls):
        self._ptr = ptr

        # Setting the class type (e.g., Point, Polygon, etc.)
        if type(self) in (GEOSGeometryBase, GEOSGeometry):
            if cls is None:
                if GEOSGeometryBase._GEOS_CLASSES is None:
                    # Inner imports avoid import conflicts with GEOSGeometry.
                    from .collections import (
                        GeometryCollection,
                        MultiLineString,
                        MultiPoint,
                        MultiPolygon,
                    )
                    from .linestring import LinearRing, LineString
                    from .point import Point
                    from .polygon import Polygon

                    GEOSGeometryBase._GEOS_CLASSES = {
                        0: Point,
                        1: LineString,
                        2: LinearRing,
                        3: Polygon,
                        4: MultiPoint,
                        5: MultiLineString,
                        6: MultiPolygon,
                        7: GeometryCollection,
                    }
                cls = GEOSGeometryBase._GEOS_CLASSES[self.geom_typeid]
            self.__class__ = cls
        self._post_init()