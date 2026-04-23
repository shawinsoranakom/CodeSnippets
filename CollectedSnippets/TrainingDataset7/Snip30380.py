def test_update_custom_primary_key(self):
        with self.assertRaisesMessage(ValueError, self.pk_fields_error):
            CustomPk.objects.bulk_update([], ["name"])