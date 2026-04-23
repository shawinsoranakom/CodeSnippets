def test_cursor_executemany(self):
        # Test cursor.executemany #4896
        args = [(i, i**2) for i in range(-5, 6)]
        self.create_squares_with_executemany(args)
        self.assertEqual(Square.objects.count(), 11)
        for i in range(-5, 6):
            square = Square.objects.get(root=i)
            self.assertEqual(square.square, i**2)