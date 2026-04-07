def test_null_string_imported(self):
        "Test LayerMapping import of GeoJSON with a null string value."
        lm = LayerMapping(HasNulls, has_nulls_geojson, has_nulls_mapping)
        lm.save()
        self.assertEqual(HasNulls.objects.filter(name="None").count(), 0)
        num_empty = 1 if connection.features.interprets_empty_strings_as_nulls else 0
        self.assertEqual(HasNulls.objects.filter(name="").count(), num_empty)
        self.assertEqual(HasNulls.objects.filter(name__isnull=True).count(), 1)