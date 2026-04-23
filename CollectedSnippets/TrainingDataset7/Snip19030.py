def test_update_conflicts_unique_fields_pk(self):
        TwoFields.objects.bulk_create(
            [
                TwoFields(f1=1, f2=1, name="a"),
                TwoFields(f1=2, f2=2, name="b"),
            ]
        )

        obj1 = TwoFields.objects.get(f1=1)
        obj2 = TwoFields.objects.get(f1=2)
        conflicting_objects = [
            TwoFields(pk=obj1.pk, f1=3, f2=3, name="c"),
            TwoFields(pk=obj2.pk, f1=4, f2=4, name="d"),
        ]
        results = TwoFields.objects.bulk_create(
            conflicting_objects,
            update_conflicts=True,
            unique_fields=["pk"],
            update_fields=["name"],
        )
        self.assertEqual(len(results), len(conflicting_objects))
        if connection.features.can_return_rows_from_bulk_insert:
            for instance in results:
                self.assertIsNotNone(instance.pk)
        self.assertEqual(TwoFields.objects.count(), 2)
        self.assertCountEqual(
            TwoFields.objects.values("f1", "f2", "name"),
            [
                {"f1": 1, "f2": 1, "name": "c"},
                {"f1": 2, "f2": 2, "name": "d"},
            ],
        )