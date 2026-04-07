def test_connector_validation(self):
        msg = f"_connector must be one of {Q.AND!r}, {Q.OR!r}, {Q.XOR!r}, or None."
        with self.assertRaisesMessage(ValueError, msg):
            Q(_connector="evil")