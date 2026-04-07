def test_invalid_algorithm(self):
        msg = "'whatever' is not an algorithm accepted by the hashlib module."
        with self.assertRaisesMessage(InvalidAlgorithm, msg):
            salted_hmac("salt", "value", algorithm="whatever")