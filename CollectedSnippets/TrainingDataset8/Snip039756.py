def test_instance_class_method(self):
        """Runtime.instance() returns our singleton instance."""
        with self.assertRaises(RuntimeError):
            # No Runtime: error
            Runtime.instance()

        # Runtime instantiated: no error
        _ = Runtime(MagicMock())
        Runtime.instance()