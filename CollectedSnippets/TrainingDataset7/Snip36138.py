def test_public_vectors(self):
        for vector in self.rfc_vectors:
            result = pbkdf2(**vector["args"])
            self.assertEqual(result.hex(), vector["result"])