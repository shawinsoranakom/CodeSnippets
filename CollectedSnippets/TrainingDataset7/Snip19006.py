def test_bulk_insert_now(self):
        NullableFields.objects.bulk_create(
            [
                NullableFields(datetime_field=Now()),
                NullableFields(datetime_field=Now()),
            ]
        )
        self.assertEqual(
            NullableFields.objects.filter(datetime_field__isnull=False).count(),
            2,
        )