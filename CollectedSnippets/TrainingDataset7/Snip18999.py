def test_large_batch_mixed_efficiency(self):
        """
        Test inserting a large batch with objects having primary key set
        mixed together with objects without PK set.
        """
        with CaptureQueriesContext(connection) as ctx:
            TwoFields.objects.bulk_create(
                [
                    TwoFields(id=i if i % 2 == 0 else None, f1=i, f2=i + 1)
                    for i in range(100000, 101000)
                ]
            )
            self.assertLess(len(ctx), 10)