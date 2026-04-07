def test_nullable_datetime_imported(self):
        """LayerMapping import of GeoJSON with a nullable date/time value."""
        lm = LayerMapping(HasNulls, has_nulls_geojson, has_nulls_mapping)
        lm.save()
        self.assertEqual(
            HasNulls.objects.filter(datetime__lt=datetime.date(1994, 8, 15)).count(), 1
        )
        self.assertEqual(
            HasNulls.objects.filter(datetime="2018-11-29T03:02:52").count(), 1
        )
        self.assertEqual(HasNulls.objects.filter(datetime__isnull=True).count(), 1)