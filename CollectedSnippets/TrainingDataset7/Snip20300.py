def test_datefield_auto_now_add(self):
        """Regression test for #10970, auto_now_add for DateField should store
        a Python datetime.date, not a datetime.datetime"""
        b = RumBaba.objects.create()
        # Verify we didn't break DateTimeField behavior
        self.assertIsInstance(b.baked_timestamp, datetime.datetime)
        # We need to test this way because datetime.datetime inherits
        # from datetime.date:
        self.assertIsInstance(b.baked_date, datetime.date)
        self.assertNotIsInstance(b.baked_date, datetime.datetime)