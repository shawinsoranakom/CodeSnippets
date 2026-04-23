def test_cursor_executemany_with_pyformat_iterator(self):
        args = ({"root": i, "square": i**2} for i in range(-3, 2))
        self.create_squares(args, "pyformat", multiple=True)
        self.assertEqual(Square.objects.count(), 5)

        args = ({"root": i, "square": i**2} for i in range(3, 7))
        with override_settings(DEBUG=True):
            # same test for DebugCursorWrapper
            self.create_squares(args, "pyformat", multiple=True)
        self.assertEqual(Square.objects.count(), 9)