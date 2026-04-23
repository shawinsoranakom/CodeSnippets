def test_empty_model(self):
        NoFields.objects.bulk_create([NoFields() for i in range(2)])
        self.assertEqual(NoFields.objects.count(), 2)