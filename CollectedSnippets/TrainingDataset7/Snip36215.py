def test_naive_datetime(self):
        dt = datetime(2009, 5, 16, 5, 30, 30)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, "U"))), dt)