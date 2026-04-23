def test_extent(self):
        """
        Testing the Extent3D aggregate for 3D models.
        """
        self._load_city_data()
        # `SELECT ST_Extent3D(point) FROM geo3d_city3d;`
        ref_extent3d = (-123.305196, -41.315268, 14, 174.783117, 48.462611, 1433)
        extent = City3D.objects.aggregate(Extent3D("point"))["point__extent3d"]

        def check_extent3d(extent3d, tol=6):
            for ref_val, ext_val in zip(ref_extent3d, extent3d):
                self.assertAlmostEqual(ref_val, ext_val, tol)

        check_extent3d(extent)
        self.assertIsNone(
            City3D.objects.none().aggregate(Extent3D("point"))["point__extent3d"]
        )