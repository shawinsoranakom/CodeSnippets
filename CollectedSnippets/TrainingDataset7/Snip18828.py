def test_cursor_executemany_with_pyformat(self):
        # Support pyformat style passing of parameters #10070
        args = [{"root": i, "square": i**2} for i in range(-5, 6)]
        self.create_squares(args, "pyformat", multiple=True)
        self.assertEqual(Square.objects.count(), 11)
        for i in range(-5, 6):
            square = Square.objects.get(root=i)
            self.assertEqual(square.square, i**2)