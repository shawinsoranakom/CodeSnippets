def test_bulk_create(self):
        m = self.base_model(a=3, b=4)
        (m,) = self.base_model.objects.bulk_create([m])
        if not connection.features.can_return_rows_from_bulk_insert:
            m = self.base_model.objects.get()
        self.assertEqual(m.field, 7)