def test_subclassing(self):
        """
        GEOSGeometry subclass may itself be subclassed without being
        forced-cast to the parent class during `__init__`.
        """

        class ExtendedPolygon(Polygon):
            def __init__(self, *args, data=0, **kwargs):
                super().__init__(*args, **kwargs)
                self._data = data

            def __str__(self):
                return "EXT_POLYGON - data: %d - %s" % (self._data, self.wkt)

        ext_poly = ExtendedPolygon(((0, 0), (0, 1), (1, 1), (0, 0)), data=3)
        self.assertEqual(type(ext_poly), ExtendedPolygon)
        # ExtendedPolygon.__str__ should be called (instead of
        # Polygon.__str__).
        self.assertEqual(
            str(ext_poly), "EXT_POLYGON - data: 3 - POLYGON ((0 0, 0 1, 1 1, 0 0))"
        )
        self.assertJSONEqual(
            ext_poly.json,
            '{"coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]], "type": "Polygon"}',
        )