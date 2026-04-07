def test_null_number_imported(self):
        """LayerMapping import of GeoJSON with a null numeric value."""
        lm = LayerMapping(HasNulls, has_nulls_geojson, has_nulls_mapping)
        lm.save()
        self.assertEqual(HasNulls.objects.count(), 3)
        self.assertEqual(HasNulls.objects.filter(num=0).count(), 1)
        self.assertEqual(HasNulls.objects.filter(num__isnull=True).count(), 1)