def test_null_number_imported_not_allowed(self):
        """
        LayerMapping import of GeoJSON with nulls to fields that don't permit
        them.
        """
        lm = LayerMapping(DoesNotAllowNulls, has_nulls_geojson, has_nulls_mapping)
        lm.save(silent=True)
        # When a model fails to save due to IntegrityError (null in non-null
        # column), subsequent saves fail with "An error occurred in the current
        # transaction. You can't execute queries until the end of the 'atomic'
        # block." On Oracle and MySQL, the one object that did load appears in
        # this count. On other databases, no records appear.
        self.assertLessEqual(DoesNotAllowNulls.objects.count(), 1)