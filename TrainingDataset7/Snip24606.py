def test_to_python(self):
        """
        to_python() either returns a correct GEOSGeometry object or
        a ValidationError.
        """
        good_inputs = [
            "POINT(5 23)",
            "MULTIPOLYGON(((0 0, 0 1, 1 1, 1 0, 0 0)))",
            "LINESTRING(0 0, 1 1)",
        ]
        bad_inputs = [
            "POINT(5)",
            "MULTI   POLYGON(((0 0, 0 1, 1 1, 1 0, 0 0)))",
            "BLAH(0 0, 1 1)",
            '{"type": "FeatureCollection", "features": ['
            '{"geometry": {"type": "Point", "coordinates": [508375, 148905]}, '
            '"type": "Feature"}]}',
        ]
        fld = forms.GeometryField()
        # to_python returns the same GEOSGeometry for a WKT
        for geo_input in good_inputs:
            with self.subTest(geo_input=geo_input):
                self.assertEqual(
                    GEOSGeometry(geo_input, srid=fld.widget.map_srid),
                    fld.to_python(geo_input),
                )
        # but raises a ValidationError for any other string
        for geo_input in bad_inputs:
            with self.subTest(geo_input=geo_input):
                with self.assertRaises(ValidationError):
                    fld.to_python(geo_input)