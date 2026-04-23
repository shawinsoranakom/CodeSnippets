def test_askml(self):
        # Should throw a TypeError when trying to obtain KML from a
        # non-geometry field.
        with self.assertRaises(TypeError):
            City.objects.annotate(kml=functions.AsKML("name"))

        # Ensuring the KML is as expected.
        ptown = City.objects.annotate(kml=functions.AsKML("point", precision=9)).get(
            name="Pueblo"
        )
        self.assertEqual(
            "<Point><coordinates>-104.609252,38.255001</coordinates></Point>", ptown.kml
        )