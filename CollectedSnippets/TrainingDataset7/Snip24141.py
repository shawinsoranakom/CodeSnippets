def _load_polygon_data(self):
        bbox_wkt, bbox_z = bbox_data
        bbox_2d = GEOSGeometry(bbox_wkt, srid=32140)
        bbox_3d = Polygon(
            tuple((x, y, z) for (x, y), z in zip(bbox_2d[0].coords, bbox_z)), srid=32140
        )
        Polygon2D.objects.create(name="2D BBox", poly=bbox_2d)
        Polygon3D.objects.create(name="3D BBox", poly=bbox_3d)