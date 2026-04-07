def test_id_field_option(self):
        """
        By default Django uses the pk of the object as the id for a feature.
        The 'id_field' option can be used to specify a different field to use
        as the id.
        """
        cities = City.objects.order_by("name")
        geojson = serializers.serialize("geojson", cities, id_field="name")
        geodata = json.loads(geojson)
        self.assertEqual(geodata["features"][0]["id"], cities[0].name)