def test_uuids_imported(self):
        """LayerMapping import of GeoJSON with UUIDs."""
        lm = LayerMapping(HasNulls, has_nulls_geojson, has_nulls_mapping)
        lm.save()
        self.assertEqual(
            HasNulls.objects.filter(
                uuid="1378c26f-cbe6-44b0-929f-eb330d4991f5"
            ).count(),
            1,
        )