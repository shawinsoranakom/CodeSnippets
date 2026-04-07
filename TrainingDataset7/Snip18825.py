def test_cursor_executemany_with_empty_params_list(self):
        # Test executemany with params=[] does nothing #4765
        args = []
        self.create_squares_with_executemany(args)
        self.assertEqual(Square.objects.count(), 0)