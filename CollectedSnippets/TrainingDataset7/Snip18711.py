def test_sqlite_date_trunc(self):
        msg = "Unsupported lookup type: 'unknown-lookup'"
        with self.assertRaisesMessage(ValueError, msg):
            _sqlite_date_trunc("unknown-lookup", "2005-08-11", None, None)