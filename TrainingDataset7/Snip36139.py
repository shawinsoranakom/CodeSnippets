def test_regression_vectors(self):
        for vector in self.regression_vectors:
            result = pbkdf2(**vector["args"])
            self.assertEqual(result.hex(), vector["result"])