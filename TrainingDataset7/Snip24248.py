def test_srid_option(self):
        geojson = serializers.serialize(
            "geojson", City.objects.order_by("name"), srid=2847
        )
        geodata = json.loads(geojson)
        coordinates = geodata["features"][0]["geometry"]["coordinates"]
        # Different PROJ versions use different transformations, all are
        # correct as having a 1 meter accuracy.
        self.assertAlmostEqual(coordinates[0], 1564802, -1)
        self.assertAlmostEqual(coordinates[1], 5613214, -1)