def test_epoch(self):
        udt = datetime(1970, 1, 1, tzinfo=UTC)
        self.assertEqual(format(udt, "U"), "0")