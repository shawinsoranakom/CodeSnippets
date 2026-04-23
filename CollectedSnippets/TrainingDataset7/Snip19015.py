def test_nullable_fk_after_parent_bulk_create(self):
        parent = NoFields()
        child = NullableFields(auto_field=parent, integer_field=88)
        NoFields.objects.bulk_create([parent])
        NullableFields.objects.bulk_create([child])
        child = NullableFields.objects.get(integer_field=88)
        self.assertEqual(child.auto_field, parent)