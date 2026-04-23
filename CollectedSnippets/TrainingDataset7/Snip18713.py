def test_sqlite_time_trunc(self):
        msg = "Unsupported lookup type: 'unknown-lookup'"
        with self.assertRaisesMessage(ValueError, msg):
            _sqlite_time_trunc("unknown-lookup", "2005-08-11 1:00:00", None, None)