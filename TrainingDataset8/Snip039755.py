def test_multiple_runtime_error(self):
        """Creating multiple Runtimes raises an error."""
        Runtime(MagicMock())
        with self.assertRaises(RuntimeError):
            Runtime(MagicMock())