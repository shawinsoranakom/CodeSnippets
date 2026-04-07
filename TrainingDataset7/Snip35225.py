def test_failure(self):
        with self.assertRaises(TypeError):
            with CaptureQueriesContext(connection):
                raise TypeError