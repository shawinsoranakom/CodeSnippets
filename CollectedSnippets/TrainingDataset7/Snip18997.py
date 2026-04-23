def test_large_batch_efficiency(self):
        with CaptureQueriesContext(connection) as ctx:
            TwoFields.objects.bulk_create(
                [TwoFields(f1=i, f2=i + 1) for i in range(0, 1001)]
            )
            self.assertLess(len(ctx), 10)