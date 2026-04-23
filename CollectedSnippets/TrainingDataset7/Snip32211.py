def test_invalid_sep(self):
        """should warn on invalid separator"""
        msg = (
            "Unsafe Signer separator: %r (cannot be empty or consist of only A-z0-9-_=)"
        )
        separators = ["", "-", "abc"]
        for sep in separators:
            with self.assertRaisesMessage(ValueError, msg % sep):
                signing.Signer(sep=sep)