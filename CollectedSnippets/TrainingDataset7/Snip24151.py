def test_perimeter(self):
        """
        Testing Perimeter() function on 3D fields.
        """
        self._load_polygon_data()
        # Reference query for values below:
        #  `SELECT ST_Perimeter3D(poly), ST_Perimeter2D(poly)
        #      FROM geo3d_polygon3d;`
        ref_perim_3d = 76859.2620451
        ref_perim_2d = 76859.2577803
        tol = 6
        poly2d = Polygon2D.objects.annotate(perimeter=Perimeter("poly")).get(
            name="2D BBox"
        )
        self.assertAlmostEqual(ref_perim_2d, poly2d.perimeter.m, tol)
        poly3d = Polygon3D.objects.annotate(perimeter=Perimeter("poly")).get(
            name="3D BBox"
        )
        self.assertAlmostEqual(ref_perim_3d, poly3d.perimeter.m, tol)