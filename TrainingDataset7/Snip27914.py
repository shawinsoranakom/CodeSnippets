def test_save(self):
        # Insert.
        m = self.base_model(a=2, b=4)
        m.save()
        expected_num_queries = (
            0 if connection.features.can_return_columns_from_insert else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.field, 6)
        # Update.
        m.a = 4
        m.save()
        expected_num_queries = (
            0 if connection.features.can_return_rows_from_update else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.field, 8)
        # Update non-dependent field.
        self.base_model.objects.filter(pk=m.pk).update(a=6)
        m.save(update_fields=["fk"])
        with self.assertNumQueries(0):
            self.assertEqual(m.field, 8)
        # Update dependent field without persisting local changes.
        m.save(update_fields=["b"])
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.field, 10)
        # Update dependent field while persisting local changes.
        m.a = 8
        m.save(update_fields=["a"])
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(m.field, 12)