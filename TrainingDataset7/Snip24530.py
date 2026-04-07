def test_nullable_boolean_imported(self):
        """LayerMapping import of GeoJSON with a nullable boolean value."""
        lm = LayerMapping(HasNulls, has_nulls_geojson, has_nulls_mapping)
        lm.save()
        self.assertEqual(HasNulls.objects.filter(boolean=True).count(), 1)
        self.assertEqual(HasNulls.objects.filter(boolean=False).count(), 1)
        self.assertEqual(HasNulls.objects.filter(boolean__isnull=True).count(), 1)