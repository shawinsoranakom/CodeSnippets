def test_empty_objects(self):
        with self.assertNumQueries(0):
            rows_updated = Note.objects.bulk_update([], ["note"])
        self.assertEqual(rows_updated, 0)