def test_non_nullable_create(self):
        with self.assertRaises(IntegrityError):
            self.base_model.objects.create()