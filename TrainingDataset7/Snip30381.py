def test_update_inherited_primary_key(self):
        with self.assertRaisesMessage(ValueError, self.pk_fields_error):
            SpecialCategory.objects.bulk_update([], ["id"])