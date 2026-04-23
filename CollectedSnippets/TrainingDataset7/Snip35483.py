def test_null_datetime(self):
        # Regression test for #17294
        e = MaybeEvent.objects.create()
        self.assertIsNone(e.dt)