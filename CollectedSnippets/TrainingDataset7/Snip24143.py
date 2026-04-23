def test_3d_polygons(self):
        """
        Test the creation of polygon 3D models.
        """
        self._load_polygon_data()
        p3d = Polygon3D.objects.get(name="3D BBox")
        self.assertTrue(p3d.poly.hasz)
        self.assertIsInstance(p3d.poly, Polygon)
        self.assertEqual(p3d.poly.srid, 32140)