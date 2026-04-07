def test_fields_option(self):
        """
        The fields option allows to define a subset of fields to be present in
        the 'properties' of the generated output.
        """
        PennsylvaniaCity.objects.create(
            name="Mansfield", county="Tioga", point="POINT(-77.071445 41.823881)"
        )
        geojson = serializers.serialize(
            "geojson",
            PennsylvaniaCity.objects.all(),
            fields=("county", "point"),
        )
        geodata = json.loads(geojson)
        self.assertIn("county", geodata["features"][0]["properties"])
        self.assertNotIn("founded", geodata["features"][0]["properties"])
        self.assertNotIn("pk", geodata["features"][0]["properties"])