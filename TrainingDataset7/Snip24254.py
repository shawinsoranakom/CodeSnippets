def test_proxy(self):
        "Testing Lazy-Geometry support (using the GeometryProxy)."
        # Testing on a Point
        pnt = Point(0, 0)
        nullcity = City(name="NullCity", point=pnt)
        nullcity.save()

        # Making sure TypeError is thrown when trying to set with an
        #  incompatible type.
        for bad in [5, 2.0, LineString((0, 0), (1, 1))]:
            with self.assertRaisesMessage(TypeError, "Cannot set"):
                nullcity.point = bad

        # Now setting with a compatible GEOS Geometry, saving, and ensuring
        #  the save took, notice no SRID is explicitly set.
        new = Point(5, 23)
        nullcity.point = new

        # Ensuring that the SRID is automatically set to that of the
        #  field after assignment, but before saving.
        self.assertEqual(4326, nullcity.point.srid)
        nullcity.save()

        # Ensuring the point was saved correctly after saving
        self.assertEqual(new, City.objects.get(name="NullCity").point)

        # Setting the X and Y of the Point
        nullcity.point.x = 23
        nullcity.point.y = 5
        # Checking assignments pre & post-save.
        self.assertNotEqual(
            Point(23, 5, srid=4326), City.objects.get(name="NullCity").point
        )
        nullcity.save()
        self.assertEqual(
            Point(23, 5, srid=4326), City.objects.get(name="NullCity").point
        )
        nullcity.delete()

        # Testing on a Polygon
        shell = LinearRing((0, 0), (0, 90), (100, 90), (100, 0), (0, 0))
        inner = LinearRing((40, 40), (40, 60), (60, 60), (60, 40), (40, 40))

        # Creating a State object using a built Polygon
        ply = Polygon(shell, inner)
        nullstate = State(name="NullState", poly=ply)
        self.assertEqual(4326, nullstate.poly.srid)  # SRID auto-set from None
        nullstate.save()

        ns = State.objects.get(name="NullState")
        self.assertEqual(connection.ops.Adapter._fix_polygon(ply), ns.poly)

        # Testing the `ogr` and `srs` lazy-geometry properties.
        self.assertIsInstance(ns.poly.ogr, gdal.OGRGeometry)
        self.assertEqual(ns.poly.wkb, ns.poly.ogr.wkb)
        self.assertIsInstance(ns.poly.srs, gdal.SpatialReference)
        self.assertEqual("WGS 84", ns.poly.srs.name)

        # Changing the interior ring on the poly attribute.
        new_inner = LinearRing((30, 30), (30, 70), (70, 70), (70, 30), (30, 30))
        ns.poly[1] = new_inner
        ply[1] = new_inner
        self.assertEqual(4326, ns.poly.srid)
        ns.save()
        self.assertEqual(
            connection.ops.Adapter._fix_polygon(ply),
            State.objects.get(name="NullState").poly,
        )
        ns.delete()