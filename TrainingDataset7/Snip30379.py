def test_update_primary_key(self):
        with self.assertRaisesMessage(ValueError, self.pk_fields_error):
            Note.objects.bulk_update([], ["id"])