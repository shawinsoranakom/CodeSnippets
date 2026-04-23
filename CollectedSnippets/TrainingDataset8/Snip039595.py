def test_builtins(self):
        """Tes code with builtins."""

        def code_with_print():
            print(12)

        def code_with_type():
            type(12)

        self.assertNotEqual(get_hash(code_with_print), get_hash(code_with_type))