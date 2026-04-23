def test_unsaved_parent(self):
        parent = NoFields()
        msg = (
            "bulk_create() prohibited to prevent data loss due to unsaved "
            "related object 'auto_field'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            NullableFields.objects.bulk_create([NullableFields(auto_field=parent)])