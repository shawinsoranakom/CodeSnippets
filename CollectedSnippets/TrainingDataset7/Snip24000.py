def test06_spatial_filter(self):
        "Testing the Layer.spatial_filter property."
        ds = DataSource(get_ds_file("cities", "shp"))
        lyr = ds[0]

        # When not set, it should be None.
        self.assertIsNone(lyr.spatial_filter)

        # Must be set a/an OGRGeometry or 4-tuple.
        with self.assertRaises(TypeError):
            lyr._set_spatial_filter("foo")

        # Setting the spatial filter with a tuple/list with the extent of
        # a buffer centering around Pueblo.
        with self.assertRaises(ValueError):
            lyr._set_spatial_filter(list(range(5)))
        filter_extent = (-105.609252, 37.255001, -103.609252, 39.255001)
        lyr.spatial_filter = (-105.609252, 37.255001, -103.609252, 39.255001)
        self.assertEqual(OGRGeometry.from_bbox(filter_extent), lyr.spatial_filter)
        feats = [feat for feat in lyr]
        self.assertEqual(1, len(feats))
        self.assertEqual("Pueblo", feats[0].get("Name"))

        # Setting the spatial filter with an OGRGeometry for buffer centering
        # around Houston.
        filter_geom = OGRGeometry(
            "POLYGON((-96.363151 28.763374,-94.363151 28.763374,"
            "-94.363151 30.763374,-96.363151 30.763374,-96.363151 28.763374))"
        )
        lyr.spatial_filter = filter_geom
        self.assertEqual(filter_geom, lyr.spatial_filter)
        feats = [feat for feat in lyr]
        self.assertEqual(1, len(feats))
        self.assertEqual("Houston", feats[0].get("Name"))

        # Clearing the spatial filter by setting it to None. Now
        # should indicate that there are 3 features in the Layer.
        lyr.spatial_filter = None
        self.assertEqual(3, len(lyr))