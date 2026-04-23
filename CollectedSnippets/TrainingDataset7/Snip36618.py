def test_to_path_invalid_value(self):
        with self.assertRaises(TypeError):
            to_path(42)