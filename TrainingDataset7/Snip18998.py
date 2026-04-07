def test_large_batch_mixed(self):
        """
        Test inserting a large batch with objects having primary key set
        mixed together with objects without PK set.
        """
        TwoFields.objects.bulk_create(
            [
                TwoFields(id=i if i % 2 == 0 else None, f1=i, f2=i + 1)
                for i in range(100000, 101000)
            ]
        )
        self.assertEqual(TwoFields.objects.count(), 1000)
        # We can't assume much about the ID's created, except that the above
        # created IDs must exist.
        id_range = range(100000, 101000, 2)
        self.assertEqual(TwoFields.objects.filter(id__in=id_range).count(), 500)
        self.assertEqual(TwoFields.objects.exclude(id__in=id_range).count(), 500)