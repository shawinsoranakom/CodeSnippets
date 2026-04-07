def test_update_conflicts_unique_fields_update_fields_db_column(self):
        FieldsWithDbColumns.objects.bulk_create(
            [
                FieldsWithDbColumns(rank=1, name="a"),
                FieldsWithDbColumns(rank=2, name="b"),
            ]
        )
        self.assertEqual(FieldsWithDbColumns.objects.count(), 2)

        conflicting_objects = [
            FieldsWithDbColumns(rank=1, name="c"),
            FieldsWithDbColumns(rank=2, name="d"),
        ]
        results = FieldsWithDbColumns.objects.bulk_create(
            conflicting_objects,
            update_conflicts=True,
            unique_fields=["rank"],
            update_fields=["name"],
        )
        self.assertEqual(len(results), len(conflicting_objects))
        if connection.features.can_return_rows_from_bulk_insert:
            for instance in results:
                self.assertIsNotNone(instance.pk)
        self.assertEqual(FieldsWithDbColumns.objects.count(), 2)
        self.assertCountEqual(
            FieldsWithDbColumns.objects.values("rank", "name"),
            [
                {"rank": 1, "name": "c"},
                {"rank": 2, "name": "d"},
            ],
        )