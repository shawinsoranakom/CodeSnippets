def test_deconstructible(self):
        """
        Geometry classes should be deconstructible.
        """
        point = Point(4.337844, 50.827537, srid=4326)
        path, args, kwargs = point.deconstruct()
        self.assertEqual(path, "django.contrib.gis.geos.point.Point")
        self.assertEqual(args, (4.337844, 50.827537))
        self.assertEqual(kwargs, {"srid": 4326})

        ls = LineString(((0, 0), (1, 1)))
        path, args, kwargs = ls.deconstruct()
        self.assertEqual(path, "django.contrib.gis.geos.linestring.LineString")
        self.assertEqual(args, (((0, 0), (1, 1)),))
        self.assertEqual(kwargs, {})

        ls2 = LineString([Point(0, 0), Point(1, 1)], srid=4326)
        path, args, kwargs = ls2.deconstruct()
        self.assertEqual(path, "django.contrib.gis.geos.linestring.LineString")
        self.assertEqual(args, ([Point(0, 0), Point(1, 1)],))
        self.assertEqual(kwargs, {"srid": 4326})

        ext_coords = ((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))
        int_coords = ((0.4, 0.4), (0.4, 0.6), (0.6, 0.6), (0.6, 0.4), (0.4, 0.4))
        poly = Polygon(ext_coords, int_coords)
        path, args, kwargs = poly.deconstruct()
        self.assertEqual(path, "django.contrib.gis.geos.polygon.Polygon")
        self.assertEqual(args, (ext_coords, int_coords))
        self.assertEqual(kwargs, {})

        lr = LinearRing((0, 0), (0, 1), (1, 1), (0, 0))
        path, args, kwargs = lr.deconstruct()
        self.assertEqual(path, "django.contrib.gis.geos.linestring.LinearRing")
        self.assertEqual(args, ((0, 0), (0, 1), (1, 1), (0, 0)))
        self.assertEqual(kwargs, {})

        mp = MultiPoint(Point(0, 0), Point(1, 1))
        path, args, kwargs = mp.deconstruct()
        self.assertEqual(path, "django.contrib.gis.geos.collections.MultiPoint")
        self.assertEqual(args, (Point(0, 0), Point(1, 1)))
        self.assertEqual(kwargs, {})

        ls1 = LineString((0, 0), (1, 1))
        ls2 = LineString((2, 2), (3, 3))
        mls = MultiLineString(ls1, ls2)
        path, args, kwargs = mls.deconstruct()
        self.assertEqual(path, "django.contrib.gis.geos.collections.MultiLineString")
        self.assertEqual(args, (ls1, ls2))
        self.assertEqual(kwargs, {})

        p1 = Polygon(((0, 0), (0, 1), (1, 1), (0, 0)))
        p2 = Polygon(((1, 1), (1, 2), (2, 2), (1, 1)))
        mp = MultiPolygon(p1, p2)
        path, args, kwargs = mp.deconstruct()
        self.assertEqual(path, "django.contrib.gis.geos.collections.MultiPolygon")
        self.assertEqual(args, (p1, p2))
        self.assertEqual(kwargs, {})

        poly = Polygon(((0, 0), (0, 1), (1, 1), (0, 0)))
        gc = GeometryCollection(Point(0, 0), MultiPoint(Point(0, 0), Point(1, 1)), poly)
        path, args, kwargs = gc.deconstruct()
        self.assertEqual(path, "django.contrib.gis.geos.collections.GeometryCollection")
        self.assertEqual(
            args, (Point(0, 0), MultiPoint(Point(0, 0), Point(1, 1)), poly)
        )
        self.assertEqual(kwargs, {})