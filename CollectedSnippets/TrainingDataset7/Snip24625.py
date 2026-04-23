def test_invalid_values(self):
        bad_inputs = [
            "POINT(5)",
            "MULTI   POLYGON(((0 0, 0 1, 1 1, 1 0, 0 0)))",
            "BLAH(0 0, 1 1)",
            '{"type": "FeatureCollection", "features": ['
            '{"geometry": {"type": "Point", "coordinates": [508375, 148905]}, '
            '"type": "Feature"}]}',
        ]
        for input in bad_inputs:
            with self.subTest(input=input):
                self.assertIsNone(BaseGeometryWidget().deserialize(input))