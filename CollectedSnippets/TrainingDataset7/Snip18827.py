def test_cursor_execute_with_pyformat(self):
        # Support pyformat style passing of parameters #10070
        args = {"root": 3, "square": 9}
        self.create_squares(args, "pyformat", multiple=False)
        self.assertEqual(Square.objects.count(), 1)