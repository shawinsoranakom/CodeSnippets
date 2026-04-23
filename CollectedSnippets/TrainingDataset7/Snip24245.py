def test_geometry_field_option(self):
        """
        When a model has several geometry fields, the 'geometry_field' option
        can be used to specify the field to use as the 'geometry' key.
        """
        MultiFields.objects.create(
            city=City.objects.first(),
            name="Name",
            point=Point(5, 23),
            poly=Polygon(LinearRing((0, 0), (0, 5), (5, 5), (5, 0), (0, 0))),
        )

        geojson = serializers.serialize("geojson", MultiFields.objects.all())
        geodata = json.loads(geojson)
        self.assertEqual(geodata["features"][0]["geometry"]["type"], "Point")

        geojson = serializers.serialize(
            "geojson", MultiFields.objects.all(), geometry_field="poly"
        )
        geodata = json.loads(geojson)
        self.assertEqual(geodata["features"][0]["geometry"]["type"], "Polygon")

        # geometry_field is considered even if not in fields (#26138).
        geojson = serializers.serialize(
            "geojson",
            MultiFields.objects.all(),
            geometry_field="poly",
            fields=("city",),
        )
        geodata = json.loads(geojson)
        self.assertEqual(geodata["features"][0]["geometry"]["type"], "Polygon")