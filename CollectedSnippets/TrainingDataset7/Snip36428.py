def test_to_base36_errors(self):
        for n in ["1", "foo", {1: 2}, (1, 2, 3), 3.141]:
            with self.assertRaises(TypeError):
                int_to_base36(n)